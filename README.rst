########
tuxeatpi
########

.. image:: https://circleci.com/gh/TuxEatPi/tuxeatpi/tree/master.svg?style=svg
    :target: https://circleci.com/gh/TuxEatPi/tuxeatpi/tree/master

.. image:: https://codeclimate.com/github/TuxEatPi/tuxeatpi/badges/gpa.svg
   :target: https://codeclimate.com/github/TuxEatPi/tuxeatpi
   :alt: Code Climate

.. image:: https://codeclimate.com/github/TuxEatPi/tuxeatpi/badges/coverage.svg
   :target: https://codeclimate.com/github/TuxEatPi/tuxeatpi/coverage
   :alt: Test Coverage

Poor Tux needs a new heart. We do that by feeding it a raspberrypi.

The end goal is to keep Tux's basic functionnality:

- Wings position detection, push buttons and movement
- Mouth movement and position detection
- Eyes position detection, photodetector and lights
- Head button
- Speaker and microphone
- Volume button


Other features considered:

- Voice recognition
- Webcam
- Voice synthesizer

Documentation
#############

https://tuxeatpi.github.io/tuxeatpi


Set dev env
###########

Install make::

    apt-get install make

Then run the following commands::

    make dep-dev
    make env-dev

Quick test
##########

Start GPIOSim::

    make gpiosim

Then the example::

    make tux_example

Then you can interact with green pin and see events in the output
