
## References

* https://github.com/joergschultzelutter/robotframework-demorobotlibrary
* https://tech.bertelsmann.com/en/blog/articles/workshop-create-a-robot-framework-keyword-library-with-python


# Getting started

1. Create a new virtual environment

    ```sh
    python3 -m venv env
    ```

2. Switch to the new interpreter in VS Code (the one with `venv` in the name)

3. On the console, activate the environment

    ```sh
    source env/bin/activate
    ```

4. Install dependencies

    ```sh
    python3 -m pip install -r requirements.txt
    ```

# TODO

* Cumulocity
    * Check parent child relationship
    * Get managed object and compare name
    * Send configuration file to device as operation

* Json comparison
    * Value matches pattern
    * Value is equal (support comparing subsections of json)


* Child devices
    * Configure child device
    * Purge child device information from the filesystem
    * Subscribe to mqtt and then PUT to http server
    * 

* Tedge
    * [x] Reconnect tedge

        ```
        sudo tedge disconnect c8y
        sudo tedge connect c8y
        ```
    * [x] Set tedge config

        ```
        sudo tedge config set mqtt.external.bind_address $value
        ```

* Device adapter
    * `List Directories In Directory`
    * [x] Directory is empty / not empty
    * [x] Directory exists / not exists
    * [x] Start/stop/restart systemd service? abstract to service manager?
