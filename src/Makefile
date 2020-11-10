pi:
	rsync -r -e 'ssh -J remote.moe' ./ pi@smartmanualstation.remote.moe:SmartManualStationPython

piclean: 
	rsync -r --delete -e 'ssh -J remote.moe' ./ pi@smartmanualstation.remote.moe:SmartManualStationPython


pi2:
	rsync -rv -e'ssh -J remote.moe' ./ pi@smartmanualstationdanfoss.remote.moe:SmartManualStationPython
pi2clean:
	rsync -rv -e 'ssh -J remote.moe' --delete ./ pi@smartmanualstationdanfoss.remote.moe:SmartManualStationPython
