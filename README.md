# ctrlX AB Data Layer Provider

The app finds AB controllers on the local network and in the same subnet as the ctrlX and puts all variables onto the datalayer. 

This work is an extension of the [pylogix  project](https://pypi.org/project/pylogix/) and the [pycomm3 project](https://pypi.org/project/pycomm3/).

## Preparation

After installation connect an AB controller to the local network of the core. Restart the core. Verify the data is available on the datalayer of the core. This data is also available on the OPC-UA server of the core if equipped. 

A config.json file is located in the app data of the controller under the AllenBradley folder. This config file can be used to configure the app to provide data from specific controllers, programs and tag lists. 

```json
{
  "LOG LEVEL": "DEBUG", // Set diagnostic log output level
  "ctrlX provider": { // Settings related to the ctrlX datalayer provider
    "local": false, // True if deployed on a local target. IP and port are unnecessary in this case
    "ip":"192.168.1.100", // IP address of target ctrlX device
    "port":"443" // Port of target ctrlX device
  },    
  "scan": false, // True if EIP network scanning is enabled. All tags are imported in this case
  "controllers": [ // Array of controllers to establish connection to
    {
      "name": "Machine1", // Controller name. Unused in logic and purely for user
      "ip": "192.168.1.50", // IP address of controller
      "tags": [ // Controller level tag import list. Remove this key to import all controller scoped tags
        "iTest",
        "bTest"
      ],
      "programs": [ // Array of controller programs to import tags from
        {
          "name": "MainProgram", // Program name in PLC
          "tags": ["arData100"] // Program level tag import list. Remove this key to import all program scoped tags
        },
        {
          "name": "SecondProgram"
        }
      ]
    }
  ]
}
```
 
___

## License

MIT License

Copyright (c) 2021-2022 Bosch Rexroth AG

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
