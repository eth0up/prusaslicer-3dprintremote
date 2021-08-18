<h1 align="center">prusaslicer-3dprintremote</h1>

<p align="center">Remotely fetch STLs, slice using PrusaSlicer console, and upload/print to Octoprint. Start a 3d print from your smartphone!
</p>

## Links

- [Repo](https://github.com/eth0up/prusaslicer-3dprintremote "prusaslicer-3dprintremote Repo")

- [Bugs](https://github.com/eth0up/prusaslicer-3dprintremote/issues "Issues/Requests Page")

<!-- ABOUT THE PROJECT -->
## About The Project

While browsing 3d model sites I often wished that I could somehow slice and send to printer directly from my smartphone. When I learned about the ability to use PrusaSlicer from the console, I started thinking about what I'd need to make my wish become reality.

For the first pass, I had these features in mind:
* Download an STL from a provided URL - I'd need some sort of server running on my designated slicing machine in order to handle URL get requests.
* Provide the downloaded STL to the console slicer (configured with my desired slicing profile) and keep note of the resultant gcode file.
* Send the gcode file to Octoprint instance and invoke the print. All as automated as possible, of course! :smile:

I came up with this project to serve my immediate wish. No single approach/workflow is the "right way" and your needs may be different. I'll be adding additional functionality in the future and I welcome your suggestions. Feel free to suggest changes by forking this repo and creating a pull request or opening an issue. 

<!-- GETTING STARTED -->

### Prerequisites

You'll need the following things in place before you can start using this project:
* Python 3 (I am using Python 3.8) with pip installed
    - https://stackoverflow.com/questions/6587507/how-to-install-pip-with-python-3
* An instance of PrusaSlicer that has at least one profile configured
* prusa-slicer-console.exe and PrusaSlicer.dll
    - If you don't see prusa-slicer-console.exe within the same directory as PrusaSlicer.exe, update your PrusaSlicer installation. At minimum, this project will need to have read access to a directory containing both prusa-slicer-console.exe and PrusaSlicer.dll.

### Installation

1. Clone the repo
   ```git clone https://github.com/eth0up/prusaslicer-3dprintremote.git```
2. In PrusaSlicer, export the profiles you would like to use 
   ```PrusaSlicer -> File -> Export -> Export Config```
   - Ensure you have exported as *.ini file(s)
3. Place exported ini files in the PROFILES folder of your local repo
4. Open a terminal and navigate to the directory of your local repo
5. Install the Python modules via pip:
```python -m pip install -r requirements.txt```
 - NOTE: As of this publish, the current OctoRest release (v0.4) does NOT contain my start-print-flag fix. Ensure you are installing the version of octorest found in requirements.txt. If manually installing modules as opposed to doing so via the above command, you can run the following to get an octorest build containing my fix: ```python -m pip install https://github.com/eth0up/OctoRest/archive/eth0up-start-print-fix.zip```
6. Edit 3dprintremote.py ```# Global Variables``` section to match your environment
7. Start the server from a terminal: ```python 3dprintremote.py```
8. Using a web browser, navigate to the host:port that you configured in 3dprintremote.py global variables section

### Global Variables

|   Variable Name  |                         Explanation                        |            Original Value            |                                                        Valid Values                                                        |
|:----------------:|:----------------------------------------------------------:|:------------------------------------:|:--------------------------------------------------------------------------------------------------------------------------:|
|                  |                                                            |                                      |                                                                                                                            |
|    FLASK_HOST    |   Hostname or IP Address where the Flask server will run   |                0.0.0.0               | An IP or Hostname on your network that can be reached (value of "0.0.0.0" binds to all available addresses on the machine) |
|    FLASK_PORT    |   Port where the Flask server will listen for connections  |                 5000                 |                              Any port number on the machine that is accessible on your network                             |
|    FLASK_DEBUG   | Controls whether Debug mode is enabled on the Flask server |                 False                |                                                        True or False                                                       |
|      STLPATH     |           Path where the STLs will be downloaded           |                 /STL                 |                                Must be a path you for which you have read/write permissions                                |
| ROOTPROFILESPATH |      Path where the PrusaSlicer profiles will be read      |               /PROFILES              |                                Must be a path you for which you have read/write permissions                                |
|  PRUSASLICERPATH |    Path to prusa-slicer-console.exe and PrusaSlicer.dll    | C:\Program Files\Prusa3D\PrusaSlicer |  Any valid system path for which you have read permissions and that contains prusa-slicer-console.exe and PrusaSlicer.dll  |
|    CURRENTPATH   |      Binds to the current working directory via function      |               getcwd()               |                                               Recommended not to change this                                               |
|   OCTO_ENABLED   |     Enables/Disables the sending of gcode to Octoprint     |                 True                 |                                    True Or False (set False if you do not use Octoprint)                                   |
|     OCTO_HOST    |         Hostname or IP Address of Octoprint server         |        https://192.168.XXX.XXX       |                             A hostname or IP address of a running instance of Octoprint server                             |
|    OCTO_APIKEY   |          API Key used to access Octoprint remotely         |   1234567890ABCDEFGHIJKLMNOPQRSTUV   |                                   Octoprint API key found in Settings -> Application Keys                                  |

<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to be learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/CoolNewFeature`)
3. Commit your Changes with comment (`git commit -m 'Add some Cool New Feature'`)
4. Push to the Branch (`git push origin feature/CoolNewFeature`)
5. Open a Pull Request

## Future Updates

- [ ] STL Upload
- [ ] INI Upload

## Author

**@eth0up**

- [Profile](https://github.com/eth0up "eth0up")

<!-- ACKNOWLEDGEMENTS -->
## Acknowledgements
* [@esgire](https://github.com/esgire) - Code review/testing and the awesome UI work

## 🤝 Support

Contributions, issues, and feature requests are welcome!

Give a ⭐️ if you like this project!
