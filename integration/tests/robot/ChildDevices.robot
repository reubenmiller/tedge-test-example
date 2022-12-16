*** Settings ***
Library    Cumulocity
Library    ThinEdgeIO

Test Teardown    Get Device Logs

*** Test Cases ***

Create child device without supported operations
    ${DEVICE_SN}=                            Setup Device
    Device Should Exist                      ${DEVICE_SN}
    Sleep    5s
    ${CHILD_NAME}=                           Get Random Name
    Execute Command On Device                mkdir -p /etc/tedge/operations/c8y/${CHILD_NAME}
    Should Be A Child Device Of Device       ${CHILD_NAME}


Create child device with supported operations
    ${DEVICE_SN}=                            Setup Device
    Device Should Exist                      ${DEVICE_SN}
    Sleep                                    5s
    ${CHILD_NAME}=                           Get Random Name
    Execute Command On Device                mkdir -p /etc/tedge/operations/c8y/${CHILD_NAME}
    Execute Command On Device                touch /etc/tedge/operations/c8y/${CHILD_NAME}/c8y_Restart
    Should Be A Child Device Of Device       ${CHILD_NAME}
    Set Device                               ${CHILD_NAME}
    ${MO}=                                   Device Should Have Fragments    c8y_SupportedOperations
    Should Match     ${MO}      *"c8y_Restart"*
