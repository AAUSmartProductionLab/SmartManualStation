pi:
	rsync -r -e 'ssh -J remote.moe' ./ pi@smartmanualstation.remote.moe:SmartManualStationPython

piclean: 
	rsync -r --delete -e 'ssh -J remote.moe' ./ pi@smartmanualstation.remote.moe:SmartManualStationPython


pi2:
	rsync -r ./ pi@192.168.1.171:SmartManualStationPython
pi2clean:
	rsync -r --delete ./ pi@192.168.1.171:SmartManualStationPython
