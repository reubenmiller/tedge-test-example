*** Settings ***
Library    Cumulocity
Library    DeviceLibrary

Test Teardown    Get Device Logs

*** Test Cases ***
Software list should be populated during startup
    ${DEVICE_SN}=                            Given Start Device
    Then Device Should Exist                      ${DEVICE_SN}
    And Device Should Have Installed Software    tedge-full

Install software via Cumulocity
    ${DEVICE_SN}=                            Start Device
    Device Should Exist                      ${DEVICE_SN}
    ${OPERATION}=    Install Software        c8y-remoteaccess-plugin
    Operation Should Be SUCCESSFUL           ${OPERATION}
    Device Should Have Installed Software    c8y-remoteaccess-plugin
