<!DOCTYPE html>
<body style="background-color:#E6E6EA">
<h3 style="text-align:center;" >Tame Audio Settings</h3>

<img src="static/Audio_Icon.jpg" alt="Audio" width="60" height="60" align="Right">

<form action="/updatepg" method = "get" >


The Min and Max audio level between 7AM and 4PM        <input name="MorMin"  type="text" size="4" maxlength="2" value="{{ MorMin }}" /> <input name="MorMax"  type="text" size="4" maxlength="2" value="{{ MorMax }}" /> db</p>
The Min and Max audio level between 4:01PM and 12AM    <input name="EveMin" type="text" size="4" maxlength="2" value="{{ EveMin }}" /> <input name="EveMax" type="text" size="4" maxlength="2" value="{{ EveMax }}" /> db</p>

The Min And Max audio level between 12:01AM and 6:59AM <input name="NigMin" type="text" size="4" maxlength="2" value="{{ NigMin }}" /> <input name="NigMax" type="text" size="4" maxlength="2" value="{{ NigMax }}"/> db</p>


<input type="submit" name = "change" value="SAVE"/>
</form>

</html>
