*** Settings ***
Library    Cumulocity
Library    DeviceLibrary

Test Teardown    Get Device Logs

*** Test Cases ***
Create a custom measurement
    ${DEVICE_SN}=                       Start Device
    Wait For Device To Be Ready
    Execute Device Command              tedge mqtt pub tedge/measurements '{"temperature": 21.3}'
    Cumulocity.Device Should Exist      ${DEVICE_SN}
    ${MEAUREMENTS}=    Device Should Have Measurements     minimum=1
    Should Match   ${MEAUREMENTS[0]}    *"temperature": {"temperature": {"value": 21.3}}*
