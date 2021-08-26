"""
GUI for viewing multiple quicklook plots at once
"""

import pathlib
import tkinter
from tkinter import ttk
from PIL import ImageTk, Image

from tqdm import tqdm
import parse


class QuicklookGrid(ttk.Frame):
    """Frame to hold multiple quicklook viewers
    """
    def __init__(self, path, lookup, parent, *args, **kwargs):
        self.path = path
        self.lookup = lookup
        self.parent = parent

        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.grid()

        self.bind("<KeyPress>", self.keydown)
        self.focus_set()

        self.button = ttk.Button(self, text="+", command=self.spawn_viewer)
        self.button.grid()

        self.viewers = []

    def keydown(self, event):
        # Use keypresses to change the parameters for all figures at once
        for viewer in self.viewers:
            # Up/Down for vertical level
            if event.keysym == "Up":
                advance(viewer.vertical_level, viewer.vertical_levels)
            elif event.keysym == "Down":
                advance(viewer.vertical_level, viewer.vertical_levels, direction=-1)

            # Left/right for timestep
            elif event.keysym == "Right":
                advance(viewer.lead_time, viewer.lead_times)
            elif event.keysym == "Left":
                advance(viewer.lead_time, viewer.lead_times, direction=-1)

            # w/s for for variable
            elif event.keysym == "w":
                advance(viewer.variable, viewer.variables)
            elif event.keysym == "s":
                advance(viewer.variable, viewer.variables, direction=-1)

            # a/d for resolution
            elif event.keysym == "d":
                advance(viewer.resolution, viewer.resolutions)
            elif event.keysym == "a":
                advance(viewer.resolution, viewer.resolutions, direction=-1)

            viewer.update_figure()

    def spawn_viewer(self, *args, **kwargs):
        self.button.grid_forget()
        self.viewers.append(QuicklookViewer(self.path, self.lookup, self))
        self.button.grid(row=0, column=4 * len(self.viewers))
        self.focus_set()


class QuicklookViewer(ttk.Frame):
    def __init__(self, path, lookup, parent, *args, **kwargs):
        self.path = path
        self.lookup = lookup

        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.grid(row=0, column=len(self.parent.viewers))

        # Create set of drop down menus
        # Drop down menu for resolution
        self.resolution = tkinter.StringVar()
        self.resolution.set(self.resolutions[0])
        self.resolution_selector = ttk.OptionMenu(
            self,
            self.resolution,
            self.resolution.get(),
            *self.resolutions,
            command=self.update_figure,
        )

        # Drop down menu for variables
        self.variable = tkinter.StringVar()
        self.variable.set(self.variables[0])
        self.variable_selector = ttk.OptionMenu(
            self,
            self.variable,
            self.variable.get(),
            *self.variables,
            command=self.update_figure,
        )

        # Drop down menu for lead times
        self.lead_time = tkinter.StringVar()
        self.lead_time.set(self.lead_times[0])
        self.lead_time_selector = ttk.OptionMenu(
            self,
            self.lead_time,
            self.lead_time.get(),
            *self.lead_times,
            command=self.update_figure,
        )

        # Drop down menu for vertical levels
        self.vertical_level = tkinter.StringVar()
        self.vertical_level.set(self.vertical_levels[0])
        self.vertical_level_selector = ttk.OptionMenu(
            self,
            self.vertical_level,
            self.vertical_level.get(),
            *self.vertical_levels,
            command=self.update_figure,
        )

        self.resolution_selector.grid(row=0, column=0, in_=self)
        self.variable_selector.grid(row=0, column=1, in_=self)
        self.lead_time_selector.grid(row=0, column=2, in_=self)
        self.vertical_level_selector.grid(row=0, column=3, in_=self)

        self.image = None
        self.figure = ttk.Label()
        self.figure.grid(row=1, column=0, columnspan=4, in_=self)
        self.set_figure()

    @property
    def resolutions(self):
        return sorted(list(self.lookup.keys()))

    @property
    def variables(self):
        return sorted(self.lookup[self.resolution.get()]["varnames"])

    @property
    def lead_times(self):
        return sorted(self.lookup[self.resolution.get()]["lead_times"])

    @property
    def vertical_levels(self):
        if self.variable.get() in self.lookup[self.resolution.get()]["levels"]:
            vertical_levels = sorted(
                self.lookup[self.resolution.get()]["levels"][self.variable.get()]
            )
        else:
            vertical_levels = ["None"]

        return vertical_levels

    def set_figure(self):
        if self.vertical_level.get() == "None":
            filename = str(
                self.path
                / self.resolution.get()
                / "{name}_T+{lead_time}.png".format(
                    name=self.variable.get(),
                    lead_time=self.lead_time.get(),
                )
            )
        else:
            filename = str(
                self.path
                / self.resolution.get()
                / "{name}_altitude{vertical_level}_T+{lead_time}.png".format(
                    name=self.variable.get(),
                    vertical_level=self.vertical_level.get(),
                    lead_time=self.lead_time.get(),
                )
            )

        self.image = ImageTk.PhotoImage(Image.open(filename))
        self.figure.configure(image=self.image)

    def update_figure(self, *args):
        self.resolution_selector.set_menu(self.resolution.get(), *self.resolutions)
        self.variable_selector.set_menu(self.variable.get(), *self.variables)
        self.lead_time_selector.set_menu(self.lead_time.get(), *self.lead_times)
        self.vertical_level_selector.set_menu(
            self.vertical_level.get(), *self.vertical_levels
        )

        try:
            self.set_figure()
        except FileNotFoundError:
            # If we changed between single-level fields and multi-level fields
            # set the vertical_level to a reasonable value
            self.vertical_level.set(self.vertical_levels[0])
            self.set_figure()


def advance(variable, iterator, direction=1):
    try:
        idx = iterator.index(variable.get()) % len(iterator)
        variable.set(iterator[idx + direction])
    except ValueError:
        idx = iterator.index(int(variable.get())) % len(iterator)
        variable.set(str(iterator[idx + direction]))


def conjure_categories(path):
    """

    Look for all pngs in the path. They are generated by quicklook.py and organised into
    folders by resolution. Each resolution has a number of variables associated to it
    and each variable can have a number of vertical levels and lead times associated to
    it. We want to get all of these associations as a nested dictionary so that we can
    use them for drop downs when selecting images.

    Args:
        path:

    Returns:

    """
    # Get a list of the resolutions (each directory in the path)
    resolutions = [d.name for d in path.glob("*") if d.is_dir()]

    # For each directory find a list of all unique variables using the file patterns
    # from quicklook.py
    lookup = dict()
    for resolution in resolutions:
        lookup[resolution] = dict(
            varnames=[],
            lead_times=[],
            levels=dict(),
        )
        plots = [f.name for f in (path / resolution).glob("*.png")]

        for plot in tqdm(plots):
            # TODO: Only have altitude at the moment but will need to format the
            #  filenames in a more parseable way in future for more coordinates
            if "altitude" in plot:
                result = parse.parse(
                    "{name}_altitude{vertical_level:d}_T+{lead_time:02d}.png", plot
                ).named

                if result["name"] not in lookup[resolution]["levels"].keys():
                    lookup[resolution]["levels"][result["name"]] = []

                if (
                    result["vertical_level"]
                    not in lookup[resolution]["levels"][result["name"]]
                ):
                    lookup[resolution]["levels"][result["name"]].append(
                        result["vertical_level"]
                    )

            else:
                result = parse.parse("{name}_T+{lead_time:02d}.png", plot).named

            if result["name"] not in lookup[resolution]["varnames"]:
                lookup[resolution]["varnames"].append(result["name"])

            if result["lead_time"] not in lookup[resolution]["lead_times"]:
                lookup[resolution]["lead_times"].append(result["lead_time"])

    return lookup


def main():
    path = pathlib.Path(".")
    lookup = conjure_categories(path)

    root = tkinter.Tk()
    root.wm_title("Moisture tracers quicklook")
    app = QuicklookGrid(path, lookup, root)
    app.mainloop()


if __name__ == "__main__":
    main()
