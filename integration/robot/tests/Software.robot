*** Settings ***
Resource    ../resources/common.resource
Library    Cumulocity
Library    ThinEdgeIO

Test Teardown    Get Device Logs

*** Test Cases ***
Software list should be populated during startup
    ${DEVICE_SN}=                                Given Setup Device
    Then Device Should Exist                     ${DEVICE_SN}~
    And Device Should Have Installed Software    tedge-full

Install software via Cumulocity
    ${DEVICE_SN}=                            Setup Device
    Device Should Exist                      ${DEVICE_SN}
    ${OPERATION}=    Install Software        c8y-remoteaccess-plugin
    Operation Should Be SUCCESSFUL           ${OPERATION}
    Device Should Have Installed Software    c8y-remoteaccess-plugin
