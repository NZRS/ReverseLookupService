__author__ = 'secastro'


from reverse_lookup import ReverseLookupService

s = ReverseLookupService()
print s.lookup_many(["130.123.3.185", "218.100.21.14", "202.50.233.38", "192.100.53.6", "Nothin", "192.168.1.1"])
