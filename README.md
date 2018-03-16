# Choregraphe Disconnector
## About
ChoregrapheDisconnector is a software that lets you remove the Choregraphe Connection from the Robot in case you didn't disconnected correctly.

ChoregrapheDisconnector works on Nao and is licensed under the Apache License 2.0.

## How it works
Upload the script on the robot, for instance to `/home/nao/disconnector.py`, then edit the `/home/nao/naoqi/preferences/autoload.ini` file to have:

`[python]`<br/>
`/home/nao/disconnector.py`

Then restart NAOqi.

## Requirements
* A Nao Robot.

## Help needed
You can help me by <a href="https://github.com/Fabrimat/Nao-ChoregrapheDisconnector/issues">proposing improvements or reporting bugs</a>.

## License
ChoregrapheDisconnector is licensed under the Apache License 2.0. See [LICENSE](LICENSE) for more information.

## Project Status & Download
ChoregrapheDisconnector's current version is **0.7.1**. You can download the latest release from <a href="https://github.com/Fabrimat/Nao-ChoregrapheDisconnector/releases/tag/v0.7.1">here</a>. Otherwise you can get the latest development version by cloning this repository.
