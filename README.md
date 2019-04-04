# Fast NAO
## English
### About
FastNAO is a software that can be installed on your Nao and lets you take the control without the use of any other devices. It can be very useful when you can't connect to the robot and you want to enable WiFi Tethering or when you want to disconnect it from Choregraphe without perform a restart.

FastNAO has been tested only on Nao H25 (V5) with Naoqi 2.1.4 and is licensed under the Apache License 2.0.

### How to install
1. Upload the script on the robot via SFTP (using FileZilla or another client) to `/home/nao/app/fastnao.py` (or wherever you want). Do not forget the inc/ folder!
2. Using an SSH client such as Putty, edit the autoload.ini file using `nano /home/nao/naoqi/preferences/autoload.ini` and append this code:<br/>
	`[python]`<br/>
	`/home/nao/app/fastnao.py`
3. Restart Naoqi using `nao restart` command.

Now you just have to press 3 times the Nao's chest button to start FastNAO and then use the head sensors to move between the options.

### Requirements
* A Nao Robot with Naoqi 2.1.4.

### Help needed
You can help me by <a href="https://github.com/Fabrimat/FastNAO/issues">proposing improvements or reporting bugs</a>.

### License
FastNAO is licensed under the Apache License 2.0. See [LICENSE](LICENSE) for more information.

### Project Status & Download
FastNAO's current version is **v0.10.1**. You can download the latest release from <a href="https://github.com/Fabrimat/FastNAO/releases/tag/v0.10.1">here</a>. Otherwise you can get the latest development version by cloning this repository.

## Italiano
### Cosa è
FastNao è un programma che può essere installato sul Nao e permette di prenderne il controllo senza il bisogno di altri dispositivi, può essere molto utile quando non ci si riesce a connettere al robot e si vuole abilitare il Tethering WiFi oppure quando si vuole disconnettere Choregraphe senza il bisogno di effettuare un riavvio.

FastNAO è stato testato solo su un Nao H25 (V5) con Naoqi 2.1.4 ed è rilasciato sotto licenza Apache 2.0.

### Come si installa
1. Carica lo script sul robot via SFTP (utilizzando Filezilla o un qualunque altro client) in `/home/nao/app/fastnao.py` (o dove preferisci). Non dimenticare la cartella inc/!
2. Effettuando l'accesso via SSH (utlizzando Putty o un qualunque altro client) modifica il file autoload.ini con il comando `nano /home/nao/naoqi/preferences/autoload.ini` e aggiungi il seguente codice:<br/>
	`[python]`<br/>
	`/home/nao/app/fastnao.py`
3. Riavvia Naoqi utilizzando il comando `nao restart`.

Adesso devi premere 3 volte il pulsante sul petto del Nao per avviare FastNAO e successivamente utilizzate i pulsanti touch posizionati sulla testa per spostarti tra le opzioni.

### Requisiti
* Un robot Nao con Naoqi 2.1.4.

### Aiutami
Puoi aiutarmi <a href="https://github.com/Fabrimat/FastNAO/issues">proponendo miglioramenti o segnalando eventuali bug</a>.

### Licenza
FastNAO è rilasciato sotto licenza Apache 2.0. Clicca su [Licenza](LICENSE) per maggiori informazioni.

### Stato del progetto & Download
La versione attuale di FastNAO è **v0.10.1**. Puoi scaricare l'ultima release da <a href="https://github.com/Fabrimat/FastNAO/releases/tag/v0.10.1">qui</a>. Altrimenti puoi ottenere l'ultima versione di sviluppo clonando questo repository.
