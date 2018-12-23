# Remember Last Position Totem Plugin

Remember last position ([Totem](https://github.com/GNOME/totem) Plugin) starts a video at the playback position that it was last paused.
In addition, it supports automatically starting the last video, at the last playback position, once Totem starts.

# Installation
Download the content of this repository to `~/.local/share/totem/plugins/remember-last-position-totem-plugin`.
Or clone the repository to the plugins folder:
```bash
cd ~/.local/share/totem/plugins
git clone https://github.com/fonaro/remember-last-position-totem-plugin.git
```

Finally, enable the plugin in the "Preferences->General->Plugins..." menu.


# How it works

During video playback, the plugin stores the current video time offset, along with its file path,
in `remember-last-position.pydata` inside the
plugin folder.

Later, when this file will be opened, the playback will continue from the last playback position, even if Totem was closed.

If load-on-start feature is enabled (disabled by default),
the plugin will start playing the last played video once Totem starts.
The playback will start only after 5 seconds (default).

*_WARNING!_ Not tested on web-sources.*

# Tuning

It is possible to tune the plugin parameters via the configuration file:
`remember-last-position.conf`.

+ `load-on-start`: Explained above (true or false).
+ `load-on-start-delay`: The time to wait for the video to start (seconds).
+ `history-length`: How many files will be stored (integer).
+ `update-interval`: Update the video playback position on interval (seconds).

## Special Thanks:
Thanks to Asanka's Weblog for quick start:
http://asanka-abeyweera.blogspot.com/2012/03/writing-plugins-for-totem-movie-player.html
