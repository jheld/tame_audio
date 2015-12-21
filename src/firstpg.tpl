<!DOCTYPE html>
<head>
  <title> Project 1 </title>
</head>
<body style="background-color:#E6E6EA">
<h1 style="text-align:center;" >Tame Audio</h1>

<!--<p>The Current audio level in db : </p>-->

<h3 style="text-align:center;" >Current Audio level  Settings</h3>

<img src="static/Audio_Icon.jpg" alt="Audio" width="60" height="60" align="Right">

<form action="/settings" method="Get">

<p>The Min And Max audio level between 7AM and 4PM in db: Min:{{MorMin}}, Max: {{MorMax}}</p>
<p>The Min And Max audio level between 4:01PM and 12AM in db    : Min:{{EveMin}}, Max: {{EveMax}}</p>
<p>The Min And Max audio level between 12:01AM and 6:59AM in db : Min:{{NigMin}}, Max: {{NigMax}}</p>

<input type="submit" name = "change" value="EDIT">

</form>
</html>


