DIST_SOURCE_DIR = $(DIST_DIR)/$(BMN_SHORT_NAME)
DIST_TARGET = $(DIST_DIR)/$(BMN_SHORT_NAME)-$(BMN_VERSION_STRING)-setup${EXEC_SUFFIX}

NSIS_CONFIG = $(BUILD_DIR)/config.nsh
NSIS_SOURCE = $(CONTRIB_PLATFORM_DIR)/setup.nsi

.PHONY: $(NSIS_CONFIG)
$(NSIS_CONFIG):
	$(file  >$@,\
		!define BMN_MAINTAINER "$(BMN_MAINTAINER)")
	$(file >>$@,\
		!define BMN_MAINTAINER_URL "$(BMN_MAINTAINER_URL)")
	$(file >>$@,\
		!define BMN_NAME "$(BMN_NAME)")
	$(file >>$@,\
		!define BMN_SHORT_NAME "$(BMN_SHORT_NAME)")
	$(file >>$@,\
		!define BMN_VERSION_STRING "$(BMN_VERSION_STRING)")
	$(file >>$@,\
		!define DIST_SOURCE_DIR "$(call NPATH,$(abspath $(DIST_SOURCE_DIR)))")
	$(file >>$@,\
		!define DIST_TARGET "$(call NPATH,$(abspath $(DIST_TARGET)))")
	$(file >>$@,\
		!define DIST_TARGET_FILE_NAME "$(notdir $(DIST_TARGET))")
	$(file >>$@,\
		!define DIST_TARGET_NAME_RELEASE "$(TARGET_NAME_RELEASE)")
	$(file >>$@,\
		!define DIST_TARGET_NAME_DEBUG "$(TARGET_NAME_DEBUG)")

dist:: $(NSIS_CONFIG)
	$(MAKENSIS) /V3 /WX /INPUTCHARSET UTF8\
		"/X!include /CHARSET=UTF8 \"$(call NPATH,$(abspath $(NSIS_CONFIG)))\""\
		"$(call NPATH,$(NSIS_SOURCE))"

dist-clean::
	$(call RM,$(NSIS_CONFIG))
