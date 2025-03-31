from enum import Enum


class LicenseType(str, Enum):
	SD = "spamDetection"
	PD = "phishingDetection"
	SPD = "spamAndPhishingDetection"

class APIKeyType(str, Enum):
	ORG = "organization"
	USR = "user"

threshold = 50