import ES2EEPROMUtils

eeprom = ES2EEPROMUtils.ES2EEPROM()
eeprom.clear(4096)

name = "jet" 
toAdd = []
score = 4

name2 = "cia"
score2 = 7

name3 = "pau"
score3 = 9

for character in name:
    toAdd.append(ord(character))
toAdd.append(score)

for character in name2:
    toAdd.append(ord(character))
toAdd.append(score2)

for character in name3:
    toAdd.append(ord(character))
toAdd.append(score3)


eeprom.write_byte(0x00, 3)
eeprom.write_block(0x20,toAdd)

reading1 = eeprom.read_byte(0x00)

reading2 = eeprom.read_block(0x20,24)


print(reading1)

readname = ""

print(reading2)
for character in reading2:
    readname += chr(character)


print(readname)



