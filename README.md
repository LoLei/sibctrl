# SteelSeries Siberia 350 control software for Linux

This program lets you change the settings on your Siberia 350 headset.
It has not been tested with other SteelSeries headsets.

Dependencies: `apt-get install python3-libusb1`

The USB device must be writable by you. The easy way is to run this as
root or chmod the device in /dev/bus/usb. The better way is to add a
rule for the headset under /dev/udev/rules.d/.

## Control the color

```
sibctrl.py --color 'ff1b00'    # orange, the best color
sibctrl.py --color '00ff00'    # green, sometimes also the best color
```

## Automatic microphone optimization

```
sibctrl.py --mic-auto          # microphone level adjusts itself
sibctrl.py --no-mic-auto       # back to the default
```

## Equalizer

The headset sports a built-in equalizer with filters tuned to 80 Hz,
280 Hz, 1 kHz, 3.5 kHz and 13 kHz. Each filter can be set
independently to a value between -12 dB to 12 dB in 0.5 dB increments.

```
sibctrl.py --equalizer=0,0,0,0,0    # set all to 0.0 dB
sibctrl.py --equalizer=6.5,,,,      # set 80 Hz to +6.5 dB
sibctrl.py --equalizer=,,-5,,       # set 1 kHz to -5.0 dB
```

## Other headset features

The surround feature of the headset is done in DSP software and is not
supported by sibctrl. There are numerous other LADSPA sound processing
plugins available under Linux. I've had luck using Bauer
stereophonic-to-binaural DSP:

```
sudo apt-get install bs2b-ladspa
pacmd load-module module-ladspa-sink sink_name=binaural \
  master=alsa_output.usb-SteelSeries_SteelSeries_Siberia_350-00.analog-stereo \
  plugin=bs2b label=bs2b control=700,4.5
```

Afterwards use `pavucontrol` to direct the playback to the LADSPA plugin.

## Ideas for improvement

Turn it into a daemon that accepts commands over a Unix domain socket
and automatically starts when the headset is hotplugged. The hardware
doesn't do any of the color animations itself and starting up sibctrl
for each color is not going to perform well.

Perhaps there is a program already that offers related types of
control for other headsets, and where this code can be integrated.

## Author

© 2018 Göran Weinholt. LGPL 3.0 or later.

## Acknowledgements

The headset is made by these awesome guys:
https://github.com/steelseries
