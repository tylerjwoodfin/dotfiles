-- Read-only: incomplete reminders on the list named Grocery.
-- Prints one line per reminder: title<TAB>notes
-- Does not complete, delete, or edit anything.

on replace_text(find_text, replace_with, subject)
	set prev_delims to AppleScript's text item delimiters
	set AppleScript's text item delimiters to find_text
	set parts to text items of subject
	set AppleScript's text item delimiters to replace_with
	set subject to parts as text
	set AppleScript's text item delimiters to prev_delims
	return subject
end replace_text

tell application "Reminders"
	set grocery_list to list "Grocery"
	set output to ""
	repeat with r in (reminders of grocery_list whose completed is false)
		set title_text to name of r as text
		set notes_text to ""
		try
			set notes_text to body of r as text
		end try
		if notes_text is "missing value" then set notes_text to ""
		set title_text to my replace_text(linefeed, " ", title_text)
		set title_text to my replace_text(return, " ", title_text)
		set notes_text to my replace_text(linefeed, " ", notes_text)
		set notes_text to my replace_text(return, " ", notes_text)
		set output to output & title_text & tab & notes_text & linefeed
	end repeat
	return output
end tell
