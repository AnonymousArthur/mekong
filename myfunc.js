  var xmlHttp;
  function GetXmlHttpObject() {
    var xmlHttp=null;
    try {
      xmlHttp=new XMLHttpRequest();   
    } catch (e) {
      try {      
        xmlHttp=new ActiveXObject("Msxml2.XMLHTTP");
      } catch (e) {
        xmlHttp=new ActiveXObject("Microsoft.XMLHTTP");
      }
    }
    return xmlHttp;
  }
  function stateChanged1() {
    if (xmlHttp.readyState==4) {
      document.getElementById('basketlistener').innerHTML = xmlHttp.responseText;
    }
  }
  function addintobasket(s) {
    xmlHttp=GetXmlHttpObject()
    if (xmlHttp==null) {
      alert ('Your browser does not support AJAX!');
      return;
    }

    xmlHttp.onreadystatechange=stateChanged1;
    try {
      xmlHttp.open('GET','mekong.cgi?addisbn='+s,true);
      xmlHttp.send(null);
      } catch(e) {
        alert ('exception error : '+e.name+'<br>'+e.message);
      }
  }
  function dropfrombasket(s) {
    xmlHttp=GetXmlHttpObject()
    if (xmlHttp==null) {
      alert ('Your browser does not support AJAX!');
      return;
    }

    xmlHttp.onreadystatechange=stateChanged1;
    try {
      xmlHttp.open('GET','mekong.cgi?dropisbn='+s,true);
      xmlHttp.send(null);
      setTimeout(window.location.reload(),5000);
      } catch(e) {
        alert ('exception error : '+e.name+'<br>'+e.message);
      }
  }
  
  
  
  function stateChanged2() {
    if (xmlHttp.readyState==4) {
      document.getElementById('orderlistener').innerHTML = xmlHttp.responseText;
    }
  }
  
  function mkorder() {
    xmlHttp=GetXmlHttpObject()
    if (xmlHttp==null) {
      alert ('Your browser does not support AJAX!');
      return;
    }
	var c;
	var m;
	var y;
	c=document.getElementById('credit');
	m=document.getElementById('month');
	y=document.getElementById('year');
    xmlHttp.onreadystatechange=stateChanged2;
    try {
      xmlHttp.open('GET','mekong.cgi?mkorder=1&credit='+c+'&date='+m+'SL'+y,true);
      xmlHttp.send(null);
      setTimeout(window.location.reload(),5000);
      } catch(e) {
        alert ('exception error : '+e.name+'<br>'+e.message);
      }
  }