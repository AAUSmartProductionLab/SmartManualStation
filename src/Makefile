
pidanfos:
	rsync -rv -e'ssh -J remote.moe' ./ pi@smartmanualstationdanfoss2.remote.moe:SmartManualStation/src
pidanfosclean:
	rsync -rv -e 'ssh -J remote.moe' --delete ./ pi@smartmanualstationdanfoss2.remote.moe:SmartManualStation/src

piremote:
	rsync -rv -e'ssh -J remote.moe' ./ pi@smartmanualstation2.remote.moe:SmartManualStation/src
piremoteclean:
	rsync -rv -e 'ssh -J remote.moe' --delete ./ pi@smartmanualstation2.remote.moe:SmartManualStation/src

pi:
	rsync -rv  ./ pi@172.20.66.25:SmartManualStation/src
piclean:
	rsync -rv  --delete ./ pi@172.20.25:SmartManualStation/src
