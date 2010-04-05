#!/usr/bin/env python

# Changes:
# -------
#
# 4: --execute command line option.
#
# 3: Error: Accept any widget.
#
# 2: Fixed miscalculation of total CPU time.
#
# 1: First public release.

"""Layer Profiler - A simple interactive profiling tool.

The Layer Profiler is an interface to profile a running program in
real time, and browse and compare profile data later.

Features
========

Multiple Profiles: The Layer Profiler uses a tabbed interface that
allows for opening and recording multiple profiles at the same time.

Loading/Saving: You can save profiles to disk, and reimport them for
browsing and comparing later. The original program is not required to
browse saved profiles. The saved files are in the CPython marshal
format.

Filtering: Profiles can be filtered, using "foo" to match and "!foo"
to exclude.

Usage
=====

There are three ways to use the Layer Profiler. The first is to run it
as a standalone executable. In this case the only thing it is capable
of profiling interactively is itself. However, you can still load and
search previously saved profiles:
  $ python -mprofiler saved.profile
  $ python ./profiler.py saved.profile

Secondly, it can be invoked to profile a program which will be
executed using excfile(); in this case it will profile the entire
program, and do it non-interatively unless the program itself starts a
GTK+ main loop. After the program finishes, the Layer Profiler
interface will appear. This can be done using:
  $ python -mprofiler --execute ./myscript.py
  $ python ./profiler.py --execute ./myscript.py

Or you can import it, start a GTK+ main loop, and instantiate a
GProfiler window. It can then profile the application that started it.
     window = MyAppWindow()
     ... # make your window here
     button = gtk.Button(_("Profile"))
     button.connect('clicked', lambda *args: GProfiler().show())
     ... # put the button in the window somehow
     gtk.main()

Some convenience methods are provided to use GTK+ in your application.

This module has no dependencies outside of PyGTK and CPython's
standard library.
"""

import os
import locale
import marshal

from cProfile import Profile

import gobject
import pango
import gtk

__all__ = ["GProfiler", "pyglet", "update"]

# If the user hasn't set up gettext translation, fake it.
try: _
except NameError: _ = lambda s: s

__version__ = 4
__author__ = "Joe Wreschnig"
__copyright__ = "Copyright 2009 Joe Wreschnig, Michael Urman"
__website__ = "http://code.google.com/p/layer/wiki/LayerProfiler"
__license__ = """\
Unless stated otherwise, BSD-style. http://yukkurigames.com/license.txt.
TreeViewHints and HintedTreeView: GNU Lesser GPL version 2.1 or later."""

UI = """<ui>
  <menubar name='Menu'>
    <menu action='Profiles'>
      <menuitem action="NewProfile" />
      <menuitem action="OpenProfile" />
      <menuitem action="SaveProfile" />
      <menuitem action="CloseProfile" />
      <separator/>
      <menuitem action="Quit" />
    </menu>
    <menu action='Help'>
      <menuitem action='About'/>
    </menu>
  </menubar>
</ui>
"""

def Error(title=None, text=None, parent=None):
    if text is None:
        text = _("An error occurred.")
    if parent is not None:
        parent = parent.get_toplevel()
    dialog = gtk.MessageDialog(parent=parent, type=gtk.MESSAGE_ERROR,
                               buttons=gtk.BUTTONS_OK,
                               message_format=title or text)
    if title:
        dialog.format_secondary_text(text)
    dialog.run()
    dialog.destroy()

def Filename(action, parent):
    d = gtk.FileChooserDialog(
        parent=parent, action=action,
        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                 gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

    if d.run() == gtk.RESPONSE_ACCEPT:
        filename = d.get_filename()
    else:
        filename = None
    d.destroy()
    return filename

# The TreeViewHints and HintedTreeView classes are licensed under the
# GNU LGPL and not the 3 clause BSD license used by the rest of Layer.
# If this is not acceptable to you, you can simply remove them from
# this file, and everything will continue working (but without useful
# tooltips).
class TreeViewHints(gtk.Window):
    """Handle 'hints' for treeviews."""

    __gsignals__ = dict.fromkeys(
        ['button-press-event', 'button-release-event',
        'motion-notify-event', 'scroll-event'],
        'override')

    def __init__(self):
        super(TreeViewHints, self).__init__(gtk.WINDOW_POPUP)
        self.__label = label = gtk.Label()
        label.set_alignment(0.5, 0.5)
        self.realize()
        self.add_events(gtk.gdk.BUTTON_MOTION_MASK | gtk.gdk.BUTTON_PRESS_MASK |
                gtk.gdk.BUTTON_RELEASE_MASK | gtk.gdk.KEY_PRESS_MASK |
                gtk.gdk.KEY_RELEASE_MASK | gtk.gdk.ENTER_NOTIFY_MASK |
                gtk.gdk.LEAVE_NOTIFY_MASK | gtk.gdk.SCROLL_MASK)
        self.add(label)

        self.set_app_paintable(True)
        self.set_resizable(False)
        self.set_name("gtk-tooltips")
        self.set_border_width(1)
        self.connect('expose-event', self.__expose)
        self.connect('enter-notify-event', self.__enter)
        self.connect('leave-notify-event', self.__check_undisplay)

        self.__handlers = {}
        self.__current_path = self.__current_col = None
        self.__current_renderer = None

    def connect_view(self, view):
        self.__handlers[view] = [
            view.connect('motion-notify-event', self.__motion),
            view.connect('scroll-event', self.__undisplay),
            view.connect('key-press-event', self.__undisplay),
            view.connect('destroy', self.disconnect_view),
        ]

    def disconnect_view(self, view):
        try:
            for handler in self.__handlers[view]: view.disconnect(handler)
            del self.__handlers[view]
        except KeyError: pass

    def __expose(self, widget, event):
        w, h = self.get_size_request()
        self.style.paint_flat_box(self.window,
                gtk.STATE_NORMAL, gtk.SHADOW_OUT,
                None, self, "tooltip", 0, 0, w, h)

    def __enter(self, widget, event):
        # on entry, kill the hiding timeout
        try: gobject.source_remove(self.__timeout_id)
        except AttributeError: pass
        else: del self.__timeout_id

    def __motion(self, view, event):
        # trigger over row area, not column headers
        if event.window is not view.get_bin_window(): return
        if event.get_state() & gtk.gdk.MODIFIER_MASK: return

        x, y = map(int, [event.x, event.y])
        try: path, col, cellx, celly = view.get_path_at_pos(x, y)
        except TypeError: return # no hints where no rows exist

        if self.__current_path == path and self.__current_col == col: return

        # need to handle more renderers later...
        try: renderer, = col.get_cell_renderers()
        except ValueError: return
        if not isinstance(renderer, gtk.CellRendererText): return
        if renderer.get_property('ellipsize') == pango.ELLIPSIZE_NONE: return

        model = view.get_model()
        col.cell_set_cell_data(model, model.get_iter(path), False, False)
        cellw = col.cell_get_position(renderer)[1]

        label = self.__label
        label.set_ellipsize(pango.ELLIPSIZE_NONE)
        label.set_text(renderer.get_property('text'))
        w, h0 = label.get_layout().get_pixel_size()
        try: markup = renderer.markup
        except AttributeError: pass
        else:
            if isinstance(markup, int): markup = model[path][markup]
            label.set_markup(markup)
            w, h1 = label.get_layout().get_pixel_size()

        if w + 5 < cellw: return # don't display if it doesn't need expansion

        x, y, cw, h = list(view.get_cell_area(path, col))
        self.__dx = x
        self.__dy = y
        y += view.get_bin_window().get_position()[1]
        ox, oy = view.window.get_origin()
        x += ox; y += oy; w += 5
        if gtk.gtk_version >= (2,8,0): w += 1 # width changed in 2.8?
        screen_width = gtk.gdk.screen_width()
        x_overflow = min([x, x + w - screen_width])
        label.set_ellipsize(pango.ELLIPSIZE_NONE)
        if x_overflow > 0:
            self.__dx -= x_overflow
            x -= x_overflow
            w = min([w, screen_width])
            label.set_ellipsize(pango.ELLIPSIZE_END)
        if not((x<=int(event.x_root) < x+w) and (y <= int(event.y_root) < y+h)):
            return # reject if cursor isn't above hint

        self.__target = view
        self.__current_renderer = renderer
        self.__edit_id = renderer.connect('editing-started', self.__undisplay)
        self.__current_path = path
        self.__current_col = col
        self.__time = event.time
        self.__timeout(id=gobject.timeout_add(100, self.__undisplay))
        self.set_size_request(w, h)
        self.resize(w, h)
        self.move(x, y)
        self.show_all()

    def __check_undisplay(self, ev1, event):
        if self.__time < event.time + 50: self.__undisplay()

    def __undisplay(self, *args):
        if self.__current_renderer and self.__edit_id:
            self.__current_renderer.disconnect(self.__edit_id)
        self.__current_renderer = self.__edit_id = None
        self.__current_path = self.__current_col = None
        self.hide()

    def __timeout(self, ev=None, event=None, id=None):
        try: gobject.source_remove(self.__timeout_id)
        except AttributeError: pass
        if id is not None: self.__timeout_id = id

    def __event(self, event):
        if event.type != gtk.gdk.SCROLL:
            event.x += self.__dx
            event.y += self.__dy 

        # modifying event.window is a necessary evil, made okay because
        # nobody else should tie to any TreeViewHints events ever.
        event.window = self.__target.get_bin_window()

        gtk.main_do_event(event)
        return True

    def do_button_press_event(self, event): return self.__event(event)
    def do_button_release_event(self, event): return self.__event(event)
    def do_motion_notify_event(self, event): return self.__event(event)
    def do_scroll_event(self, event): return self.__event(event)

class HintedTreeView(gtk.TreeView):
    """A TreeView that pops up a tooltip for truncated text."""

    def __init__(self, *args):
        super(HintedTreeView, self).__init__(*args)
        try: tvh = HintedTreeView.hints
        except AttributeError: tvh = HintedTreeView.hints = TreeViewHints()
        tvh.connect_view(self)

class ProfileModel(gtk.ListStore):
    def matches(model, column, key, iter):
        filename = model[iter][1]
        callname = model[iter][2]
        if key in filename.lower():
            return False
        elif key in callname.lower():
            return False
        else:
            return True
    matches = staticmethod(matches)
        
    def __init__(self, stats=None):
        super(ProfileModel, self).__init__(
            object, # code
            str, # filename
            str, # callable name
            int, # line number
            int, # call count
            int, # recursive call count
            float, # total time
            float, # inline time
            )
        for stat in (stats or []):
            self.append(row=stat)

    def _get_stats(self):
        return [tuple(row) for row in self]

    def _set_stats(self, stats):
        self.clear()
        filenames = set()
        for entry in stats:
            if isinstance(entry.code, str):
                filename = ("<builtin>")
                callname = entry.code
                line = 0
            else:
                filename = entry.code.co_filename
                filenames.add(filename)
                callname = entry.code.co_name
                line = entry.code.co_firstlineno
            self.append(row=[entry.code,
                             filename,
                             callname,
                             line,
                             entry.callcount,
                             entry.reccallcount,
                             entry.totaltime,
                             entry.inlinetime])

    stats = property(_get_stats, _set_stats)

class FilterEntry(gtk.Entry):
    def __init__(self, model):
        super(FilterEntry, self).__init__()
        self.connect_object('changed', self._compile, model)
        self.set_tooltip_text(
            _("Enter search terms. Use '!' as a prefix to exclude terms."))
        model.set_visible_func(self.filter)
        self._include = []
        self._exclude = []

    def _compile(self, model):
        self._include = []
        self._exclude = []
        for token in self.get_text().lower().split():
            if token[0] == '!':
                self._exclude.append(token[1:])
            else:
                self._include.append(token)
        model.refilter()
        
    def filter(self, model, iter):
        code = model[iter][0]
        if code is None: return False
        if isinstance(code, str): text = code
        else: text = code.co_name + " " + code.co_filename
        text = text.lower()
        for token in self._exclude:
            if token in text:
                return False
        for token in self._include:
            if token not in text:
                return False
        return True

class ProfilerTab(gtk.VBox):
    def __init__(self, stats=None):
        super(ProfilerTab, self).__init__()
        toolbar = gtk.HBox(spacing=6)
        self.pack_start(toolbar, expand=False, fill=True)
        self.model = ProfileModel(stats)
        self.profile = not stats and Profile()

        toggle = gtk.ToggleButton(gtk.STOCK_MEDIA_RECORD)
        toggle.set_use_stock(True)
        toggle.set_active(False)
        toggle.set_sensitive(bool(self.profile))
        toggle.connect('toggled', self.__toggle)
        toolbar.pack_start(toggle, expand=False)
        if not self.profile:
            toggle.set_tooltip_text(
                _("Loaded profiles cannot resume recording."))

        filtered = self.model.filter_new()
        align = gtk.Alignment(xscale=1.0, yscale=1.0)
        align.set_padding(0, 0, 6, 0)
        label = gtk.Label()
        self.entry = FilterEntry(filtered)
        label.set_mnemonic_widget(self.entry)
        label.set_text_with_mnemonic(_("_Filter:"))
        try: self.view = HintedTreeView(gtk.TreeModelSort(filtered))
        except NameError: self.view = gtk.TreeView(gtk.TreeModelSort(filtered))
        self.view.connect('row-activated', self.__open_to_line)
        self.view.set_enable_search(True)
        self.view.set_search_equal_func(self.model.matches)
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_IN)
        sw.add(self.view)
        box = gtk.HBox(spacing=3)
        box.pack_start(label, expand=False)
        box.pack_start(self.entry)
        align.add(box)
        self.pack_start(sw, expand=True)

        toolbar.pack_start(align)

        cell = gtk.CellRendererText()
        cell.props.ellipsize = pango.ELLIPSIZE_MIDDLE

        column = gtk.TreeViewColumn(_("Filename"), cell)
        column.add_attribute(cell, 'text', 1)
        column.set_sort_column_id(1)
        column.set_resizable(True)
        column.set_expand(True)
        self.view.append_column(column)   

        column = gtk.TreeViewColumn(_("Function"), cell)
        column.add_attribute(cell, 'text', 2)
        column.set_sort_column_id(2)
        column.set_resizable(True)
        column.set_expand(True)
        self.view.append_column(column)   

        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_("Call #"), cell)
        column.add_attribute(cell, 'text', 4)
        column.set_sort_column_id(4)
        self.view.append_column(column)   
        column = gtk.TreeViewColumn(_("Total"), cell)
        column.add_attribute(cell, 'text', 6)
        column.set_sort_column_id(6)
        self.view.append_column(column)   
        column = gtk.TreeViewColumn(_("Inline"), cell)
        column.add_attribute(cell, 'text', 7)
        column.set_sort_column_id(7)
        self.view.append_column(column)   

        self.totalstats = gtk.Statusbar()
        self.pack_start(self.totalstats, expand=False)
        
        self.entry.grab_focus()
        self.running = False
        self.connect('destroy', self.__on_destroy)

    def __on_destroy(self, *args):
        self.stop()

    def __open_to_line(self, view, path, column):
        code = view.get_model()[path][0]
        try:
            lineno = "+%d" % code.co_firstlineno
            filename = code.co_filename
        except AttributeError: pass
        else:
            args = ['sensible-editor', lineno, filename]
            gobject.spawn_async(args, flags=gobject.SPAWN_SEARCH_PATH)

    def __toggle(self, button):
        """Turn profiling on if off and vice versa."""
        if button.get_active():
            self.start()
        else:
            self.stop()

    def snapshot(self):
        """Update the UI with a snapshot of the current profile state."""
        self.model.stats = self.profile.getstats()
        totalcalls = 0
        totaltime = 0
        for entry in self.model.stats:
            totalcalls += entry[3]
            totaltime += entry[7]
        text = _("%(calls)d calls in %(time)f CPU seconds.") % dict(
            calls=totalcalls, time=totaltime)
        self.totalstats.pop(0)
        self.totalstats.push(0, text)

    def save(self, filename):
        try:
            fileobj = file(filename, "wb")
            fileobj.write(marshal.dumps(self.model.stats))
            fileobj.close()
        except Exception, err:
            err = str(err).decode(locale.getpreferredencoding(), 'replace')
            Error(_("Unable to save"), err, parent=self.get_toplevel())
        else:
            self.parent.set_tab_label_text(self, os.path.basename(filename))

    def start(self):
        """Start profiling (adding to existing stats)."""
        if not self.running and self.profile:
            self.profile.enable()
            self.running = True

    def stop(self):
        """Stop profiling (but retain stats)."""
        if self.running and self.profile:
            self.profile.disable()
            self.running = False
            self.snapshot()

class GProfiler(gtk.Window):
    """A window containing tabbed profiling data.

    The window is not visible by default. You should call .show()
    on it after it is constructed.
    """

    def __init__(self):
        """Construct a new Profiler window."""
        super(GProfiler, self).__init__()
        self.set_title(_("Layer Profiler"))
        self.set_default_size(400, 300)
        self.add(gtk.VBox())
        self.count = 0
        self.tabs = []

        self.notebook = gtk.Notebook()
        self.notebook.set_scrollable(True)
        self.notebook.connect('page-added', self.__page_count_changed)
        self.notebook.connect('page-removed', self.__page_count_changed)

        self.ui = gtk.UIManager()
        actions = gtk.ActionGroup("ProfilerActions")
        actions.add_actions(
            [('Profiles', None, _("_Profiles")),
             ('NewProfile', gtk.STOCK_NEW, None,
              None, None, self.__new_tab),
             ('OpenProfile', gtk.STOCK_OPEN, None,
              None, None, self.__open_tab),
             ('SaveProfile', gtk.STOCK_SAVE, None,
              None, None, self.__save_tab),
             ('CloseProfile', gtk.STOCK_CLOSE, None,
              None, None, self.__close_tab),
             ("Quit", gtk.STOCK_QUIT, None, None, None,
              lambda a: self.destroy()),
             ("Help", None, _("_Help")),
             ("About", gtk.STOCK_ABOUT, None, None, None, self.__about),
             ])

        self.ui.insert_action_group(actions, -1)
        self.ui.add_ui_from_string(UI)
        self.add_accel_group(self.ui.get_accel_group())
        self.child.pack_start(self.ui.get_widget("/Menu"), expand=False)
        self.child.pack_start(self.notebook)
        self.__new_tab()
        self.child.show_all()

    def __save_tab(self, *args):
        i = self.notebook.get_current_page()
        tab = self.notebook.get_nth_page(i)
        if tab:
            filename = Filename(action=gtk.FILE_CHOOSER_ACTION_SAVE,
                                parent=self)
            if filename:
                tab.save(filename)

    def __close_tab(self, *args):
        i = self.notebook.get_current_page()
        tab = self.notebook.get_nth_page(i)
        if tab and self.notebook.get_n_pages() > 1:
            self.notebook.remove_page(i)
            tab.destroy()
            self.tabs.remove(tab)

    def __page_count_changed(self, notebook, child, pagenum):
        self.ui.get_widget("/Menu/Profiles/CloseProfile").set_sensitive(
            notebook.get_n_pages() > 1)

    def __new_tab(self, *args):
        self.count += 1
        label = gtk.Label(_("Profile %d") % (self.count))
        tab = ProfilerTab()
        label.show_all()
        tab.show_all()
        self.notebook.set_current_page(self.notebook.append_page(tab, label))
        self.tabs.append(tab)

    def new(self):
        """Open a new empty profiler tab."""
        self.__new_tab()
        
    def open(self, filename):
        """Open a tab to browse the given saved profile."""
        try:
            stats = marshal.load(file(filename, "rb"))
            self.count += 1
            label = gtk.Label(os.path.basename(filename))
            tab = ProfilerTab(stats)
        except Exception, err:
            err = str(err).decode(locale.getpreferredencoding(), 'replace')
            Error(_("Unable to open"), err, parent=self.get_toplevel())
        else:
            label.show_all()
            tab.show_all()
            self.notebook.set_current_page(
                self.notebook.append_page(tab, label))
            self.ui.get_widget("/Menu/Profiles/CloseProfile").set_sensitive(
                self.notebook.get_n_pages() > 1)
        
    def __open_tab(self, filename):
        filename = Filename(action=gtk.FILE_CHOOSER_ACTION_OPEN, parent=self)
        if filename:
            self.open(filename)

    def __about(self, *args):
        a = gtk.AboutDialog()
        a.set_version(str(__version__))
        a.set_copyright(__copyright__)
        a.set_license("\n".join([__copyright__, __license__]))
        a.set_website(__website__)
        a.set_program_name(_("Layer Profiler"))
        a.set_comments(_("A simple interactive profiling tool."))
        a.connect('close', lambda *args: a.destroy())
        a.connect('response', lambda *args: a.destroy())
        a.show_all()

def update(*args, **kwargs):
    """Hook into a generic main loop.

    Calling this function once a frame will run GTK+. The arguments
    are irrelevant.
    """
    i = 0
    while gtk.events_pending() and i < 5:
        gtk.main_iteration()
        i += 1

def pyglet():
    """Hook GTK+ into the pyglet main loop.

    After calling this you can run GProfiler() as necessary, and it
    will work correctly within a running pyglet application.
    """
    import pyglet
    pyglet.clock.schedule(update)
            
if __name__ == "__main__":
    import sys
    argv = sys.argv[1:]
    filenames = []
    execute = []

    while argv:
        arg = argv.pop(0)
        if arg.lower() in ["--version", "-v", "/version", "/v"]:
            print >>sys.stderr, _(
                "Layer Profiler %d - A simple interactive profiling tool.") % (
                __version__)
            raise SystemExit
        elif arg.lower() in ["--help", "-h", "/help", "/h", "/?"]:
            print _("Usage:\t%s [filename] ... [--execute script.py ...]\n"
                    " or:\tpydoc %s") % (
                sys.argv[0],
                os.path.splitext(os.path.basename(sys.argv[0]))[0])
            raise SystemExit
        elif arg.lower() in ["--execute", "-e", "/execute", "/e",
                              "--exec", "/exec"]:
            execute = argv[:]
            argv = []
        else:
            filenames.append(arg)
    w = GProfiler()
    for filename in filenames:
        w.open(filename)
    w.connect('destroy', gtk.main_quit)
    w.show()
    if execute:
        sys.argv = execute
        sys.path.insert(0, os.path.dirname(sys.argv[0]))
        w.tabs[0].start()
        try: execfile(sys.argv[0])
        except StandardError, err:
            # stop ASAP so the error handler isn't profiled.
            w.tabs[0].stop()
            import traceback
            traceback.print_exc()
            err = traceback.format_exc().splitlines()[-1]
            Error(_("Abnormal termination"),
                  _("%s was abnormally terminated. The error was:\n%s") %(
                    sys.argv[0],
                    err.decode(locale.getpreferredencoding(), 'replace')))
        w.tabs[0].stop()
    gtk.main()
