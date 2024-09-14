set s = CreateObject("SAPI.SpVoice")

	
'Create a file; set DoEvents=True so TTS events will be saved to the file
set fs = CreateObject("FileStream")
fs.Open Wscript.Arguments(1), SSFMCreateForWrite, True

'Set the output to the FileStream
Set Voice.AudioOutputStream = fs

s.Speak Wscript.Arguments(0), 3
s.WaitUntilDone(1000)


'Close the Stream
fs.Close
'Release the objects
Set fs = Nothing
Set Voice = Nothing