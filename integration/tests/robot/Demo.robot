# https://github.com/joergschultzelutter/robotframework-demorobotlibrary
# https://tech.bertelsmann.com/en/blog/articles/workshop-create-a-robot-framework-keyword-library-with-python

*** Settings ***
Library    Cumulocity
Library    DeviceLibrary

Test Teardown    Get Device Logs

*** Test Cases ***
Create a custom measurement
    ${DEVICE_SN}=                       Start Device
    Execute Device Command              tedge mqtt pub tedge/measurements '{"value":1.234}'
    Cumulocity.Device Should Exist      ${DEVICE_SN}
    ${MEAUREMENTS}=    Device Should Have Measurements     min_count=1
    # Should Match   ${MEAUREMENTS[0].to_json()}    *1.234*
    # Should Contain    ${MEAUREMENTS[0].to_json()}    1.234
    # Device Should Have Alarm/s          min_matches=1


My Successful Test Case
    Cumulocity.Device Should Exist      tedge01
    # Import library  DebugLibrary
    # Debug
    Cumulocity.Device Should Have Fragments    owner    c8y_SupportedConfigurations
    Cumulocity.Device Should Have Child Devices    ONE    TWO
