# Fast NAO
## About
### English
FastNAO is a software that can be installed on your Nao and lets you take the control without the use of any other devices. It can be very useful when you can't connect to the robot and you want to enable WiFi Tethering or you want to disconnect it from Choregraphe without perform a restart.

FastNAO has been tested on Nao H25 and is licensed under the Apache License 2.0.

### Italiano
FastNao è un programma che può essere installato sul Nao e permette di prenderne il controllo senza il bisogno di altri dispositivi, può essere molto utile quando non ci si riesce a connettere al robot e si vuole abilitare il Tethering WiFi oppure quando si vuole disconnettere Choregraphe senza il bisogno di effettuare un riavvio.

FastNAO è stato testato su un Nao H25 ed è rilasciato sotto licenza Apache 2.0.

## How it works
Upload the script on the robot, for instance to `/home/nao/fastnao.py`, then edit the `/home/nao/naoqi/preferences/autoload.ini` file to have:

`[python]`<br/>
`/home/nao/fastnao.py`

Then restart NAOqi.  
Now, you just have to press 3 times the Nao's chest button to start FastNAO and then use the head sensors to move between the options.

## Requirements
* A Nao Robot with Naoqi 2.1.4.

## Help needed
You can help me by <a href="https://github.com/Fabrimat/FastNAO/issues">proposing improvements or reporting bugs</a>.

## License
FastNAO is licensed under the Apache License 2.0. See [LICENSE](LICENSE) for more information.

## Project Status & Download
FastNAO's current version is **Pre-release 0.8.10**. You can download the latest release from <a href="https://github.com/Fabrimat/FastNAO/releases/tag/v0.8.10">here</a>. Otherwise you can get the latest development version by cloning this repository.
