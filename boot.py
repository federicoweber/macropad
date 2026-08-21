"""Enable a second USB serial port for host-to-MacroPad metadata."""

import usb_cdc


usb_cdc.enable(console=True, data=True)
