# Requirements
- Java 17 or later
- Python 3.12
- [Ollama](https://ollama.com/)

# Installation
```sh
pip install -r requirements.txt
```
Creating and activating a virtual environment is recommended. 

# Running
To run the Conversational Agent, first start a Llama 2 instance using the following command:

```sh
ollama run llama2
```

Build the GUI using:
````sh
javac PythonOutputGUI.java
````
Then, start the agent using the following:

```sh
java PythonOutputGUI
```
