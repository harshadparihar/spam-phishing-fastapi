from enum import Enum


class LicenseType(str, Enum):
	SD = "spamDetection"
	PD = "phishingDetection"
	SPD = "spamAndPhishingDetection"

class APIKeyType(str, Enum):
	ORG = "organization"
	USR = "user"

threshold = 50

phishing_features = [
    "UsingIP", "LongURL", "ShortURL", "Symbol@", "Redirecting//", "PrefixSuffix-", "SubDomains",
    "HTTPS", "DomainRegLen", "Favicon", "NonStdPort", "HTTPSDomainURL", "RequestURL", "AnchorURL",
    "LinksInScriptTags", "ServerFormHandler", "InfoEmail", "AbnormalURL", "WebsiteForwarding",
    "StatusBarCust", "DisableRightClick", "UsingPopupWindow", "IframeRedirection", "AgeofDomain",
    "DNSRecording", "WebsiteTraffic", "PageRank", "GoogleIndex", "LinksPointingToPage", "StatsReport"
]