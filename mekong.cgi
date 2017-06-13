#!/usr/bin/perl -w
# written by yzhu028@cse.unsw.edu.au November 2013
# for COMP2041 assignment 2
# http://www.cse.unsw.edu.au/~cs2041/assignments/mekong/

use CGI qw/:all/;
use CGI::Session;
use CGI::Cookie;
use Mail::Sendmail;
use File::Copy;


$debug = 0;
$| = 1;

if (!@ARGV) {
	# run as a CGI script
	cgi_main();
	
} else {
	# for debugging purposes run from the command line
	console_main();
}
exit 0;

# This is very simple CGI code that goes straight
# to the search screen and it doesn't format the
# search results at all

# This is very simple CGI code that goes straight
# to the search screen and it doesn't format the
# search results at all

sub cgi_main {	

	set_global_variables();
	my $login = param('login');
	my $password=param('pwd');
	my $need_logout=param('logout');
	my $need_register=param('register');
	my $register_username=param('username');
	my $register_pwd=param('pwd');
	my $register_fullname=param('fullname');
	my $register_street=param('street');
	my $register_city=param('city');
	my $register_state=param('state');
	my $register_postcode=param('postcode');
	my $register_email=param('email');
	my $register_activation=param('active');
	my $key_word=param('search_terms');
	my $book_serial=param('isbn');
	my $basket_isbn=param('addisbn');
	my $basket_isbn_delete=param('dropisbn');
	my $need_basket=param('basket');
	my $mk_order=param('mkorder');
	my $order_month=param('month');
	my $order_year=param('year');
	my $order_card=param('credit');
	my $need_order=param('showorders');
	my $draw_order=param('showorder');
	my $need_about=param('about');
	my $need_profile=param('profile');
	my $activation_passed;
	my $order_complete;
	my $register_passed;
	if(defined $need_register){
		if($need_register eq 2){
			$register_passed=register_check($register_username,$register_pwd,$register_fullname,$register_street,$register_city,$register_state,$register_postcode,$register_email);
		}elsif($need_register eq 3 && $register_activation ne ""){
			if(open(TMP,"$pending_users_dir/$register_activation")){
				close(TMP);
				$activation_file="$pending_users_dir/$register_activation";
				$account_file="$users_dir/$register_activation";
				move($activation_file,$account_file) or die "The move operation failed: $!";
				$activation_passed=1;
			}else{
				$error_by="register";
				$last_error="Activation error!";
				$activation_passed=0;
			}
		}
	}
	my $session = new CGI::Session("driver:File", $cgi ,{Directory=>'/tmp'});
	my $session_user = $session->param("u_name");
	read_books($books_file);
	if(defined $basket_isbn && $basket_isbn ne "" && defined $session_user){
		print $cgi->header();
		add_command($session_user,$basket_isbn);
		print qq(<div class="alert alert-success alert-dismissable"><button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button>Book added to your basket.</div>);
		exit 0;	
	}elsif(defined $basket_isbn && $basket_isbn ne "" && !defined $session_user){
		print $cgi->header();
		print qq(<div class="alert alert-danger alert-dismissable"><button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button>Please login!</div>);
		exit 0;
	}elsif(defined $basket_isbn_delete && $basket_isbn_delete ne "" && defined $session_user){
		print $cgi->header();
		drop_command($session_user,$basket_isbn_delete);
		exit 0;
	}elsif(defined $basket_isbn_delete && $basket_isbn_delete ne "" && !defined $session_user){
		print $cgi->header();
		print "Please login!";
		exit 0;
	}elsif(defined $mk_order && $mk_order eq 1 && defined $order_month && $order_year && defined $order_card){
		my $order_date=$order_month."/".$order_year;
		$order_complete=checkout_command($session_user,$order_card,$order_date);
	}
	
	if(defined $login && defined $password && !defined $need_register){
		if(authenticate($login,$password)){	    
			print $cgi->header(-cookie=>$cookie);
			print "<script language='javascript'>";
			print " location.href='mekong.cgi'";
			print "</script>";
		}else{
			print $cgi->header();
			$error_by="login";
		}
	}elsif(defined $need_logout && $need_logout eq 1){
		logout($session);
	}else{
		print $cgi->header();
	}
	
	if(!defined $session_user){
		print page_header();
		print navi_bar(0);
	}else{
		read_user($session_user);
		print page_header();
		print navi_bar(1);
	}
	show_error();
	if(defined $need_register){
		if($need_register eq 1){
			print register_form();
		}elsif($need_register eq 2){
			if(!$register_passed){
				print register_form();
			}elsif($register_passed){
				print qq(<div class="alert alert-info">Registration email has sent to your E-mail address, please follow steps in the mail to active your account.</div>);
			}
		}		
		if($activation_passed){
			print qq(<div class="alert alert-success">Your account is now activated! Welcome to Mekong.</div>);
			print page_home();
		}
	}elsif(defined $key_word && $key_word ne ""){
		print basket_listener();	
		print search_results($key_word);
	}elsif(defined $book_serial && $book_serial ne ""){
		print basket_listener();
		print book_description($book_serial);
	}elsif(defined $need_basket && $need_basket eq 1){
		print checkout_form($session_user);
		print basket_listener();
		print basket_info($session_user);	
	}elsif(defined $need_order && $need_order eq 1){
		print show_orders($session_user);				
	}elsif(defined $draw_order && $draw_order ne ""){
		print show_order($draw_order);		
	}elsif(defined $order_complete && $order_complete eq 1){
		print show_orders($session_user);
	}elsif(defined $order_complete && $order_complete eq 0){
		print checkout_form($session_user);
		print basket_info($session_user);	
	}elsif(defined $need_about && $need_about eq 1){
		print about_page();
	}elsif(defined $need_profile && $need_profile eq 1){
		print profile($session_user);		
	}else{
		if(!defined $login){
			print page_home();
		}
	}
	print page_trailer();
}

#read user's profile
sub profile{
	my ($user)=@_;
	our(%user_details);
	my $info;
	$info=qq(
	<h1 style="text-align:left;">Your profile...</h1>
	<table class="table" style="width:400px; margin:0 auto;">
	<tr><td>Full name: </td><td>$user_details{name}</td></tr>
	<tr><td>Street: </td><td>$user_details{street}</td></tr>
	<tr><td>City: </td><td>$user_details{city}</td></tr>
	<tr><td>State: </td><td>$user_details{state}</td></tr>
	<tr><td>Postcode: </td><td>$user_details{postcode}</td></tr>
	<tr><td>E-mail address: </td><td>$user_details{email}</td></tr>
	</table>
	);
	return $info;
	
}
#draw an about page
sub about_page{
	return qq(
	<h1 style="text-align:left;">About</h1>
	<p style="text-align:left; font-size:20px; width:500px;">This website is running on UNSW CSE server and based on Perl CGI writen by Yancheng Zhu.
	In this website you can order books after you log in. And the register also provided on the top of navi bar.
	If you want to copy my code, please let me know. The icon of the this website and the homepage image is not made/taken by me. 
	My email address is unicrix at gmail.com
	</p>
	<img src="https://fbcdn-sphotos-f-a.akamaihd.net/hphotos-ak-frc3/308355_452268268197184_1969494628_n.jpg" class="img-rounded" style="width:380px; float:right;">
	);
}
#draw home page
sub page_home{
	my $info;
	$info=qq(<div class="home"><p style="font-size:50px;">Black and White.</p><p style="font-size:50px; color:#cccccc;">Not just Black and White.</p></div>);		
	return $info	
}

#show an order of an specified number
sub show_order{
	my ($order)=@_;	
	my ($order_time, $credit_card_number, $expiry_date, @isbns) = read_order($order);
	my $info;
	$credit_card_number =~s/^\d{12}/**** **** **** /;
	$order_time = localtime($order_time);
	$info=qq(<h2 style="text-align:left;">Here is your order...</h2> <h4 style="text-align:left;">Order number: $order</h4><p>Paid by credit card $credit_card_number<br>Order at $order_time<p>);
	$info.=order_book(@isbns);
	return $info;
}

#show info of book in order list
sub order_book{
	my @isbns = @_;
	my $descriptions = "";
	our %book_details;
	$descriptions .=qq(<table class="table table-hover">);
	foreach $isbn (@isbns) {
		die "Internal error: unknown isbn $isbn in print_books\n" if !$book_details{$isbn}; # shouldn't happen
		my $title = $book_details{$isbn}{title} || "";
		my $authors = $book_details{$isbn}{authors} || "";
		my $thumb_url = $book_details{$isbn}{smallimageurl} || "";
		my $price = $book_details{$isbn}{price} || "";
		$authors =~ s/\n([^\n]*)$/ & $1/g;
		$authors =~ s/\n/, /g;
		$descriptions .= qq(<tr><td><a href="mekong.cgi?isbn=$isbn"><div class="book_thumb"><img class="book_thumb_img" src="$thumb_url"></div></a></td><td><a href="mekong.cgi?isbn=$isbn">$title</a><br><br><br>$authors</td><td><div class="book_price_small"><table cellpadding="10"><tr><td>$price</td></tr><tr><td></td></tr></table></div></td><tr>);
	}
	$descriptions .= qq(</table>);
	return $descriptions;	
}


#show all orders of user
sub show_orders{
	my ($login) = @_;
	my $info=qq(<h2 style="text-align:left">Your orders...</h2><table class="table table-hover">);
	foreach $order (login_to_orders($login)) {
		my ($order_time, $credit_card_number, $expiry_date, @isbns) = read_order($order);
		$order_time = localtime($order_time);
		$credit_card_number =~s/^\d{12}/**** **** **** /;
		$info.=qq(<tr><td><a href="mekong.cgi?showorder=$order">Order #$order - $order_time</a></td><td>Credit Card Number: $credit_card_number (Expiry $expiry_date)</td></tr>);
	}
	$info.="</table>";
	if($info eq qq(<h2 style="text-align:left">Your orders...</h2><table class="table table-hover"></table>)){
		$info=qq(<h2 style="text-align:left">Your orders...</h2><div class="alert alert-info">You currently don't have any order.</div>);
	}
	return $info;
}

#check out information total price etc
sub checkout_info{
	my ($login) = @_;
	if(!defined $login){
		return "<div class='alert alert-warning'>Your have to login!</div>";
	}
	our(%user_details);
	my @basket_isbns = read_basket($login);
	my $total_price;
	$total_price=total_books(@basket_isbns);
	my $description;
	$description=qq(
	<table class="table table-hover">
	<tr><td>Your name:</td><td>$user_details{name}</td></tr>
	<tr><td>Address:</td><td>$user_details{street},$user_details{city}<br>$user_details{state} $user_details{postcode}</td></tr>
	<tr><td>Total</td><td>\$$total_price</td></tr>
	</table>	
	);	
	return $description;
}


#orderlistener
sub order_listener{
	my $object;
	$object=qq(<div id="orderlistener"></div>);
	return $object;	
}



#check out information
sub checkout_form{
	my ($user)=@_;
	my $html;
	$html=qq(
<div class="modal fade" id="checkOutWindow" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
      	<div id="orderlistener"></div> 	
        <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>       
        <h4 class="modal-title" id="myModalLabel">Check out</h4>
      </div>
      <div class="modal-body">);
      $html.=checkout_info($user);
      $html.=qq(
      </div>
      <form method="post" role="form">
      <table class="table">
      <tr><td><p style="font-size:16px; padding:2px;">Credit card:</p></td><td colspan="3"><input class="form-control" type="text" name="credit" size=12 placeholder="Credit card number"></td></tr>
      <tr><td><p style="font-size:16px; padding:2px;">Expire date:</p></td>
      <td style="right:2px;">
      <select class="form-control" name="month" style="width:65px">
      	<option value="01">1</option>
      	<option value="02">2</option>
      	<option value="03">3</option>
      	<option value="04">4</option>
      	<option value="05">5</option>
      	<option value="06">6</option>
      	<option value="07">7</option>
      	<option value="08">8</option>
      	<option value="09">9</option>
      	<option value="10">10</option>
      	<option value="11">11</option>
      	<option value="12">12</option>
      </select></td><td><p style="font-size:25px;">/</p></td><td>
      <select class="form-control" name="year" style="width:95px">
      	<option value="13">2013</option>
      	<option value="14">2014</option>
      	<option value="15">2015</option>
      	<option value="16">2016</option>
      	<option value="17">2017</option>
      </select>
      </td>
      </tr>
      </table>   
      <input type="hidden" name="mkorder" value="1"></input>        
      <div class="modal-footer">
        <button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>
        <button type="submit" class="btn btn-success">Place order</button>
      </div>
       </form> 
    </div><!-- /.modal-content -->
  </div><!-- /.modal-dialog -->
</div><!-- /.modal -->);
return $html;
}

#basketlistener
sub basket_listener{
	my $object;
	$object=qq(<div id="basketlistener"></div>);
	return $object;
}

#return the book description page correspond to ISBN
sub book_description{
	my ($isbn)=@_;
	our %book_details;
	my $title=$book_details{$isbn}{title} || "";
	my $authors=$book_details{$isbn}{authors} || "";
	my $binding=$book_details{$isbn}{binding} || "";
	my $large_img=$book_details{$isbn}{largeimageurl} || "";
	my $productdescription=$book_details{$isbn}{productdescription} || "";
	my $price=$book_details{$isbn}{price} || "";
	my $pub_date=$book_details{$isbn}{publication_date} || "";
	#my $edition=$book_details{$isbn}{edition} || "";
	my $publisher=$book_details{$isbn}{publisher} || "";
	my $description=qq(<p>
	<h1>$title</h1>
	<table>
	<tr>
	<td><img src="$large_img"></td>
	<td>
	<div class="book_infomation">
	<table class="table table-bordered">
	<tr><td>Authors: </td>
	<td>$authors</td></tr>
	<tr><td>Publisher: </td>
	<td>$publisher</td><tr>
	<tr><td>Publication Date: </td>
	<td>$pub_date</td><tr>
	<tr><td>Binding: </td>
	<td>$binding</td><tr>
	<tr><td>Price: </td>
	<td>$price</td><tr>
	<tr><td colspan="2" style="text-align:center;">
	<button type="button" class="btn btn-info" style="text-align:bottom; width:160px; height:60px;" onclick="addintobasket('$isbn')" >Add to basket</button>	
	</td>
	</tr>
	</table>
	</div>
	</td>
	</tr>
	<tr>
	<td colspan="2">
	<div class="product_description">
	$productdescription
	</div>
	</td>
	</tr>
	</table>);
	return $description;
}


#check user's registration
sub register_check{
	my ($user_name,$pwd,$fullname,$street,$city,$state,$postcode,$email)=@_;
	if($user_name eq ""|| !legal_user($user_name)){
		$error_by="register";
		if($user_name eq ""){
			$last_error="You must enter your user name.";
		}
		return 0;
	}
	if($pwd eq ""|| !legal_password($pwd)){
		$error_by="register";
		if($pwd eq ""){
			$last_error="You must enter your password.";
		}
		return 0;
	}
	if($fullname eq ""){
		$error_by="register";
		$last_error="You must enter your full name.";
		return 0;
	}
	if($street eq ""){
		$error_by="register";
		$last_error="You must enter street information.";
		return 0;
	}
	if($city eq ""){
		$error_by="register";
		$last_error="You must enter city/suburb information.";
		return 0;
	}	
	if($state eq ""){
		$error_by="register";
		$last_error="You must enter state information.";
		return 0;
	}
	if($postcode eq ""){
		$error_by="register";
		$last_error="You must enter postcode information.";
		return 0;
	}
	if($email eq ""|| !legal_email($email)){
		$error_by="register";
		if($email eq ""){
			$last_error="You must enter your email address.";
		}
		return 0;
	}
	if(send_registration_email($user_name,$pwd,$fullname,$street,$city,$state,$postcode,$email)){
		open(PENDING,">$pending_users_dir/$user_name");
		print PENDING ("login=$user_name\npassword=$pwd\nname=$fullname\nstreet=$street\ncity=$city\nstate=$state\npostcode=$postcode\nemail=$email");
		close(PENDING);
		return 1;
	}else{
		$error_by="register";
		$last_error="System not avaliable.";
		return 0;
	}
}
sub send_registration_email{	
	my ($user_name,$pwd,$fullname,$street,$city,$state,$postcode,$email)=@_;
	$message=qq(<html><head><meta http-equiv="Content-Type" content="text/html; cahrset=utf8"></head><body><h3>Hi $fullname</h3><p>Thanks for your registration. Please click <a href="http://cgi.cse.unsw.edu.au/~yzhu028/ass2/mekong.cgi?register=3&active=$user_name">here</a> to finish your registration.</p><p>From <a href="http://cgi.cse.unsw.edu.au/~yzhu028/ass2/mekong.cgi">mekong.com.au</a></p></body></html>);
	open(MAIL, "|/usr/sbin/sendmail -t");
	## Mail Header
	print MAIL "To: $email\n";
	print MAIL 'From: yzhu028@cse.unsw.edu.au\n';
	print MAIL "Subject:Welcome to mekong!\n";
	## Mail Body
	print MAIL "Content-type: text/html\n";
	print MAIL $message; 
	close(MAIL);
	return 1;
}



sub legal_email{
	my ($email)=@_;
	our($last_error);
	if($email !~ /.+@.+\..+/){
		$last_error="Invalid Email Address!";
		return 0;
	}
	return 1;
}


sub legal_user{
	my ($user_name)=@_;
	our($last_error);
	if ($user_name !~ /^[a-zA-Z][a-zA-Z0-9]*$/) {
		$last_error = "Invalid User name '$user_name': logins must start with a letter and contain only letters and digits.";
		return 0;
	}
	if (length $user_name < 3 || length $user_name > 8) {
		$last_error = "Invalid User name: logins must be 3-8 characters long.";
		return 0;
	}
	if (open(USER, "$users_dir/$user_name") || open(USER, "$pending_users_dir/$user_name")) {
		$last_error = "User '$user_name' does exist. Please choose other user name.";
		close(USER);
		return 0;
	}
	return 1;	
}



#register
sub register_form{
	return <<eof;
	<h2 style="text-align:left">Create your own account...</h2>
	<div style="margin:0 auto; width:300px;">
	<form method="post" role="form">
	<table>
	<tr>
	<td>
	<div class="input-group">
		<span class="input-group-addon" style="padding:2px; width:96px;">User name</span>
		<input type="text" class="form-control" name="username" size=16 placeholder="User name"></input>
	</div>
		<input type="hidden" name="register" value="2"></input>
	</td>
	</tr>
	<tr>
	<td>
	<div class="input-group">
		<span class="input-group-addon" style="padding:2px; width:96px;">Password</span>
		<input type="password" class="form-control" name="pwd" size=16 placeholder="Password"></input>
	</div>
	<td>
	</tr>
	<tr>
	<td>
	<div class="input-group">
		<span class="input-group-addon" style="padding:2px; width:96px;">Full name</span>
		<input type="text" class="form-control" name="fullname" size=16 placeholder="Full name"></input>
	</div>
	</td>
	</tr>
	<tr>
	<td>
	<div class="input-group">
		<span class="input-group-addon" style="padding:2px; width:96px;">Street</span>
		<input type="text" class="form-control" name="street" size=16 placeholder="Street"></input>
	</div>
	</td>
	</tr>
	<tr>
	<td>
	<div class="input-group">
		<span class="input-group-addon" style="padding:2px; width:96px;">City/Suburb</span>
		<input type="text" class="form-control" name="city" size=16 placeholder="City/Suburb"></input>
	</div>
	</td>
	</tr>
	<tr>
	<td>
	<div class="input-group">
		<span class="input-group-addon" style="padding:2px; width:96px;">State</span>
		<input type="text" class="form-control" name="state" size=16 placeholder="State"></input>
	</div>
	</td>
	</tr>
	<tr>
	<td>
	<div class="input-group">
		<span class="input-group-addon" style="padding:2px; width:96px;">Postcode</span>
		<input type="text" class="form-control" name="postcode" size=16 placeholder="Postcode"></input>
	</div>
	</td>
	</tr>
	<tr>
	<td>
	<div class="input-group">
		<span class="input-group-addon" style="padding:2px; width:96px;">Email Address</span>
		<input type="text" class="form-control" name="email" size=16 placeholder="Email Address"></input>
	</div>
	</td>
	</tr>	
	<tr>
		<td><button type="submit" class="btn btn-primary">Create Account</button><td>
	</tr>
	</table>	
	</form>
	</div>
eof
}

#show alert
sub show_error{
	if(defined $last_error){
		print <<eof;
		<div class="alert alert-danger">
		<p>$last_error</p>
		</div>
eof
	if(defined $error_by && $error_by eq "login"){
		#print "<p style='text-align:center;'>"
		print login_form();
		#print "</p>";
		$error_by=undef;
	}
		$last_error=undef;
	}	
}
#log out: clean cookie
sub logout{
	my ($session)=@_;
	$session->delete();
    $session->flush();
    my $cookie = $cgi->cookie (
                -name    => 'name',
                -value   => '',
                -path    => '/',
                -expires => '-1d'
 );
print $cgi->header(-cookie => $cookie);
print "<script language='javascript'>";
print " location.href='mekong.cgi'";
print "</script>";
}
#read user infomation
sub read_user{
	my ($login)=@_;
	if (!open(USER, "$users_dir/$login")) {
		$last_error = "User '$login' does not exist.";
		return 0;
	}
	my %details =();
	while (<USER>) {
		next if !/^([^=]+)=(.*)/;
		$details{$1} = $2;
	}
	close(USER);
	%user_details = %details;
}

#navigation bar
sub navi_bar{
	my ($islogin)=@_;
	if($islogin){
		my $user_name = $user_details{"name"};
		return <<eof;
<div class="navbar navbar-default navbar-fixed-top">
      <div class="container">
        <div class="navbar-header">
          <button type="button" class="navbar-toggle" data-toggle="collapse" data-target=".navbar-collapse">
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
          </button>
          <a class="navbar-brand" href="mekong.cgi">Mekong</a>
        </div>
        <div class="navbar-collapse collapse">
          <ul class="nav navbar-nav">
            <li><a href="mekong.cgi">Home</a></li>
            <li><a href="mekong.cgi?about=1">About</a></li>
			<li>
			<form class="search_form">	
			<div class="input-group">		
			<input type="text" name="search_terms" class="form-control" size=30 placeholder="What do you want?"></input>
			      <span class="input-group-btn">
				  <button class="btn btn-default" type="submit">Search</button>
				  </span>
			</div>
			</form>
			</li>
          </ul>
          <ul class="nav navbar-nav navbar-right">
            <li class="dropdown">
              <a href="#" class="dropdown-toggle" data-toggle="dropdown">Welcome $user_name <b class="caret"></b></a>
              <ul class="dropdown-menu">
                <li><a href="mekong.cgi?profile=1">Pro\ffile</a></li>
                <li><a href="mekong.cgi?basket=1">Basket</a></li>
                <li><a href="mekong.cgi?showorders=1">Order</a></li>
                <li class="divider"></li>
                <li><a href="mekong.cgi?logout=1">Log out</a></li>
              </ul>
            </li>
          </ul>
        </div><!--/.nav-collapse -->
      </div>
    </div>
<div class="box1">
eof
	}else{
		return <<eof;
<div class="navbar navbar-default navbar-fixed-top">
      <div class="container">
        <div class="navbar-header">
          <button type="button" class="navbar-toggle" data-toggle="collapse" data-target=".navbar-collapse">
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
          </button>
          <a class="navbar-brand" href="mekong.cgi">Mekong</a>
        </div>
        <div class="navbar-collapse collapse">
          <ul class="nav navbar-nav">
            <li><a href="mekong.cgi">Home</a></li>
            <li><a href="mekong.cgi?about=1">About</a></li>
			<li>
			<form class="search_form">	
			<div class="input-group">		
			<input type="text" name="search_terms" class="form-control" size=30 placeholder="What do you want?"></input>
			      <span class="input-group-btn">
				  <button class="btn btn-default" type="submit">Search</button>
				  </span>
			</div>
			</form>
			</li>
          </ul>
          <ul class="nav navbar-nav navbar-right">          
            <li class="dropdown">
              <a href="#" class="dropdown-toggle" data-toggle="dropdown">Log in</a>
              <ul class="dropdown-menu">
			  	<div class="login_form">
			  	<form method="post" role="form">
			  	<table>
			  	<tr>
			  	<td>
			  	<div class="input-group">
			  	<span class="input-group-addon" style="padding:2px"><img src="icon/glyphicons_003_user.png" height="20" width="20"></span>
			  	<input type="text" class="form-control" name="login" size=16 placeholder="User name"></input>
			  	</div>
			  	</td>
			  	</tr>
			  	<tr>
			  	<td>
			  	<div class="input-group">
			  	<span class="input-group-addon" style="padding:2px"><img src="icon/glyphicons_203_lock.png" height="20" width="20"></span>
			  	<input type="password" class="form-control" name="pwd" size=16 placeholder="Password"></input>
			  	</div>
			  	<td>
			  	</tr>
			  	<tr>
			  	<td><button type="submit" class="btn btn-primary">Login</button><td>
			  	</tr>
			  	</table>	
			  	</form>
			  	</div>
              </ul>
            </li>
            <li><a href="mekong.cgi?register=1">Register</a></li>
          </ul>
        </div><!--/.nav-collapse -->
      </div>
    </div>
<div class="box1">
eof
	}
}

# Login form
sub login_form {
	return <<eof;
	<div class="login_box">
	<div class="login_form">
	<form method="post" role="form">
	<table>
	<tr>
	<td>
	<div class="input-group">
		<span class="input-group-addon" style="padding:2px"><img src="icon/glyphicons_003_user.png" height="20" width="20"></span>
		<input type="text" class="form-control" name="login" size=16 placeholder="User name"></input>
	</div>
	</td>
	</tr>
	<tr>
	<td>
	<div class="input-group">
		<span class="input-group-addon" style="padding:2px"><img src="icon/glyphicons_203_lock.png" height="20" width="20"></span>
		<input type="password" class="form-control" name="pwd" size=16 placeholder="Password"></input>
	</div>
	<td>
	</tr>
	<tr>
		<td><button type="submit" class="btn btn-primary">Login</button><td>
	</tr>
	</table>	
	</form>
	</div>
	</div>
eof
}

# simple search form
sub search_form {
	return <<eof;
	<p>
	<form>
		search: <input type="text" name="search_terms" size=60></input>
	</form>
	<p>
eof
}

# ascii display of search results
sub search_results {
	my ($search_terms) = @_;
	my @matching_isbns = search_books($search_terms);	
	my $descriptions;
	$descriptions = get_book_descriptions(@matching_isbns);
	if($descriptions eq qq(<table class="table table-hover"></table>)){
		$descriptions = qq(<div class="alert alert-info">Opps. No result.</div>);
	 }
	return <<eof;
	<div class="results">
		$descriptions
	</div>
eof
}

#
# HTML at top of every screen
#
sub page_header() {
	return <<eof;
<!DOCTYPE html>
<html lang="en">
<head>
<title>Mekong</title>
<meta charset="utf-8">
<meta name="description" content="">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="http://getbootstrap.com/dist/css/bootstrap.css" rel="stylesheet">
<link href="assignment.css" rel="stylesheet">
<script src="https://code.jquery.com/jquery-1.10.2.min.js"></script>
<script src="http://getbootstrap.com/dist/js/bootstrap.min.js"></script>
<script src="myfunc.js"></script>
<link rel="icon" type="image/x-icon" href="icon/favicon.ico" />
</head>
<body>
<p>
eof
}

#
# HTML at bottom of every screen
#
sub page_trailer() {	
	return <<eof;
	</div>
	<hr style="padding:0px;">
	<p class="footer">COMP2041 Assignment 2 | Yancheng Zhu | Copyright reserved.</p>
<body>
</html>
eof
}

#
# Print out information for debugging purposes
#
sub debugging_info() {
	my $params = "";
	foreach $p (param()) {
		$params .= "param($p)=".param($p)."\n"
	}

	return <<eof;
<hr>
<h4>Debugging information - parameter values supplied to $0</h4>
<pre>
$params
</pre>
<hr>
eof
}




###
### Below here are utility functions
### Most are unused by the code above, but you will 
### need to use these functions (or write your own equivalent functions)
### 
###

# return true if specified string can be used as a login

sub legal_login {
	my ($login) = @_;
	our ($last_error);

	if ($login !~ /^[a-zA-Z][a-zA-Z0-9]*$/) {
		$last_error = "Invalid login '$login': logins must start with a letter and contain only letters and digits.";
		return 0;
	}
	if (length $login < 3 || length $login > 8) {
		$last_error = "Invalid login: logins must be 3-8 characters long.";
		return 0;
	}
	return 1;
}

# return true if specified string can be used as a password

sub legal_password {
	my ($password) = @_;
	our ($last_error);
	
	if ($password =~ /\s/) {
		$last_error = "Invalid password: password can not contain white space.";
		return 0;
	}
	if (length $password < 5) {
		$last_error = "Invalid password: passwords must contain at least 5 characters.";
		return 0;
	}
	return 1;
}


# return true if specified string could be an ISBN

sub legal_isbn {
	my ($isbn) = @_;
	our ($last_error);
	
	return 1 if $isbn =~ /^\d{9}(\d|X)$/;
	$last_error = "Invalid isbn '$isbn' : an isbn must be exactly 10 digits.";
	return 0;
}


# return true if specified string could be an credit card number

sub legal_credit_card_number {
	my ($number) = @_;
	our ($last_error);
	
	return 1 if $number =~ /^\d{16}$/;
	$last_error = "Invalid credit card number - must be 16 digits.\n";
	return 0;
}

# return true if specified string could be an credit card expiry date

sub legal_expiry_date {
	my ($expiry_date) = @_;
	our ($last_error);
	
	return 1 if $expiry_date =~ /^\d\d\/\d\d$/;
	$last_error = "Invalid expiry date - must be mm/yy, e.g. 11/04.\n";
	return 0;
}



# return total cost of specified books

sub total_books {
	my @isbns = @_;
	our %book_details;
	$total = 0;
	foreach $isbn (@isbns) {
		die "Internal error: unknown isbn $isbn  in total_books" if !$book_details{$isbn}; # shouldn't happen
		my $price = $book_details{$isbn}{price};
		$price =~ s/[^0-9\.]//g;
		$total += $price;
	}
	return $total;
}

# return true if specified login & password are correct
# user's details are stored in hash user_details

sub authenticate {
	my ($login, $password) = @_;
	our (%user_details, $last_error);
	
	return 0 if !legal_login($login);
	if (!open(USER, "$users_dir/$login")) {
		$last_error = "User '$login' does not exist.";
		return 0;
	}
	my %details =();
	while (<USER>) {
		next if !/^([^=]+)=(.*)/;
		$details{$1} = $2;
	}
	close(USER);
	foreach $field (qw(name street city state postcode password)) {
		if (!defined $details{$field}) {
 	 	 	$last_error = "Incomplete user file: field $field missing";
			return 0;
		}
	}
	if ($details{"password"} ne $password) {
  	 	$last_error = "Incorrect password.";
		return 0;
	 }
	 %user_details = %details;	 
	 my $session = new CGI::Session("driver:File", $cgi , {Directory=>'/tmp'});
	 $cookie = $cgi->cookie(CGISESSID =>$session->id); 
     $session->param('u_name', $login);  
     $session->expire('+12h');
  	 return 1;
}

# read contents of files in the books dir into the hash book
# a list of field names in the order specified in the file
 
sub read_books {
	my ($books_file) = @_;
	our %book_details;
	print STDERR "read_books($books_file)\n" if $debug;
	open BOOKS, $books_file or die "Can not open books file '$books_file'\n";
	my $isbn;
	while (<BOOKS>) {
		if (/^\s*"(\d+X?)"\s*:\s*{\s*$/) {
			$isbn = $1;
			next;
		}
		next if !$isbn;
		my ($field, $value);
		if (($field, $value) = /^\s*"([^"]+)"\s*:\s*"(.*)",?\s*$/) {
			$attribute_names{$field}++;
			print STDERR "$isbn $field-> $value\n" if $debug > 1;
			$value =~ s/([^\\]|^)\\"/$1"/g;
	  		$book_details{$isbn}{$field} = $value;
		} elsif (($field) = /^\s*"([^"]+)"\s*:\s*\[\s*$/) {
			$attribute_names{$1}++;
			my @a = ();
			while (<BOOKS>) {
				last if /^\s*\]\s*,?\s*$/;
				push @a, $1 if /^\s*"(.*)"\s*,?\s*$/;
			}
	  		$value = join("\n", @a);
			$value =~ s/([^\\]|^)\\"/$1"/g;
	  		$book_details{$isbn}{$field} = $value;
	  		print STDERR "book{$isbn}{$field}=@a\n" if $debug > 1;
		}
	}
	close BOOKS;
}

# return books matching search string

sub search_books {
	my ($search_string) = @_;
	$search_string =~ s/\s*$//;
	$search_string =~ s/^\s*//;
	return search_books1(split /\s+/, $search_string);
}

# return books matching search terms

sub search_books1 {
	my (@search_terms) = @_;
	our %book_details;
	print STDERR "search_books1(@search_terms)\n" if $debug;
	my @unknown_fields = ();
	foreach $search_term (@search_terms) {
		push @unknown_fields, "'$1'" if $search_term =~ /([^:]+):/ && !$attribute_names{$1};
	}
	printf STDERR "$0: warning unknown field%s: @unknown_fields\n", (@unknown_fields > 1 ? 's' : '') if @unknown_fields;
	my @matches = ();
	BOOK: foreach $isbn (sort keys %book_details) {
		my $n_matches = 0;
		if (!$book_details{$isbn}{'=default_search='}) {
			$book_details{$isbn}{'=default_search='} = ($book_details{$isbn}{title} || '')."\n".($book_details{$isbn}{authors} || '');
			print STDERR "$isbn default_search -> '".$book_details{$isbn}{'=default_search='}."'\n" if $debug;
		}
		print STDERR "search_terms=@search_terms\n" if $debug > 1;
		foreach $search_term (@search_terms) {
			my $search_type = "=default_search=";
			my $term = $search_term;
			if ($search_term =~ /([^:]+):(.*)/) {
				$search_type = $1;
				$term = $2;
			}
			print STDERR "term=$term\n" if $debug > 1;
			while ($term =~ s/<([^">]*)"[^"]*"([^>]*)>/<$1 $2>/g) {}
			$term =~ s/<[^>]+>/ /g;
			next if $term !~ /\w/;
			$term =~ s/^\W+//g;
			$term =~ s/\W+$//g;
			$term =~ s/[^\w\n]+/\\b +\\b/g;
			$term =~ s/^/\\b/g;
			$term =~ s/$/\\b/g;
			next BOOK if !defined $book_details{$isbn}{$search_type};
			print STDERR "search_type=$search_type term=$term book=$book_details{$isbn}{$search_type}\n" if $debug;
			my $match;
			eval {
				my $field = $book_details{$isbn}{$search_type};
				# remove text that looks like HTML tags (not perfect)
				while ($field =~ s/<([^">]*)"[^"]*"([^>]*)>/<$1 $2>/g) {}
				$field =~ s/<[^>]+>/ /g;
				$field =~ s/[^\w\n]+/ /g;
				$match = $field !~ /$term/i;
			};
			if ($@) {
				$last_error = $@;
				$last_error =~ s/;.*//;
				return (); 
			}
			next BOOK if $match;
			$n_matches++;
		}
		push @matches, $isbn if $n_matches > 0;
	}
	
	sub bySalesRank {
		my $max_sales_rank = 100000000;
		my $s1 = $book_details{$a}{SalesRank} || $max_sales_rank;
		my $s2 = $book_details{$b}{SalesRank} || $max_sales_rank;
		return $a cmp $b if $s1 == $s2;
		return $s1 <=> $s2;
	}
	
	return sort bySalesRank @matches;
}


# return books in specified user's basket

sub read_basket {
	my ($login) = @_;
	our %book_details;
	open F, "$baskets_dir/$login" or return ();
	my @isbns = <F>;

	close(F);
	chomp(@isbns);
	!$book_details{$_} && die "Internal error: unknown isbn $_ in basket\n" foreach @isbns;
	return @isbns;
}


# delete specified book from specified user's basket
# only first occurance is deleted

sub delete_basket {
	my ($login, $delete_isbn) = @_;
	my @isbns = read_basket($login);
	if(!open F, ">$baskets_dir/$login" ){
		return 0;
	}
	foreach $isbn (@isbns) {
		if ($isbn eq $delete_isbn) {
			$delete_isbn = "";
			next;
		}
		print F "$isbn\n";
	}
	close(F);
	unlink "$baskets_dir/$login" if ! -s "$baskets_dir/$login";
	return 1;
}


# add specified book to specified user's basket

sub add_basket {
	my ($login, $isbn) = @_;
	open F, ">>$baskets_dir/$login" or die "Can not open $baskets_dir/$login::$! \n";
	print F "$isbn\n";
	close(F);
}


# finalize specified order

sub finalize_order {
	my ($login, $credit_card_number, $expiry_date) = @_;
	my $order_number = 0;

	if (open ORDER_NUMBER, "$orders_dir/NEXT_ORDER_NUMBER") {
		$order_number = <ORDER_NUMBER>;
		chomp $order_number;
		close(ORDER_NUMBER);
	}
	$order_number++ while -r "$orders_dir/$order_number";
	open F, ">$orders_dir/NEXT_ORDER_NUMBER" or die "Can not open $orders_dir/NEXT_ORDER_NUMBER: $!\n";
	print F ($order_number + 1);
	close(F);

	my @basket_isbns = read_basket($login);
	open ORDER,">$orders_dir/$order_number" or die "Can not open $orders_dir/$order_number:$! \n";
	print ORDER "order_time=".time()."\n";
	print ORDER "credit_card_number=$credit_card_number\n";
	print ORDER "expiry_date=$expiry_date\n";
	print ORDER join("\n",@basket_isbns)."\n";
	close(ORDER);
	unlink "$baskets_dir/$login";
	
	open F, ">>$orders_dir/$login" or die "Can not open $orders_dir/$login:$! \n";
	print F "$order_number\n";
	close(F);
	return 1;
}


# return order numbers for specified login

sub login_to_orders {
	my ($login) = @_;
	open F, "$orders_dir/$login" or return ();
	@order_numbers = <F>;
	close(F);
	chomp(@order_numbers);
	return @order_numbers;
}



# return contents of specified order

sub read_order {
	my ($order_number) = @_;
	open F, "$orders_dir/$order_number" or warn "Can not open $orders_dir/$order_number:$! \n";
	@lines = <F>;
	close(F);
	chomp @lines;
	foreach (@lines[0..2]) {s/.*=//};
	return @lines;
}

###
### functions below are only for testing from the command line
### Your do not need to use these funtions
###

sub console_main {
	set_global_variables();
	$debug = 1;
	foreach $dir ($orders_dir,$baskets_dir,$users_dir) {
		if (! -d $dir) {
			print "Creating $dir\n";
			mkdir($dir, 0777) or die("Can not create $dir: $!");
		}
	}
	read_books($books_file);
	my @commands = qw(login new_account search details add drop basket checkout orders quit);
	my @commands_without_arguments = qw(basket checkout orders quit);
	my $login = "";
	
	print "mekong.com.au - ASCII interface\n";
	while (1) {
		$last_error = "";
		print "> ";
		$line = <STDIN> || last;
		$line =~ s/^\s*>\s*//;
		$line =~ /^\s*(\S+)\s*(.*)/ || next;
		($command, $argument) = ($1, $2);
		$command =~ tr/A-Z/a-z/;
		$argument = "" if !defined $argument;
		$argument =~ s/\s*$//;
		
		if (
			$command !~ /^[a-z_]+$/ ||
			!grep(/^$command$/, @commands) ||
			grep(/^$command$/, @commands_without_arguments) != ($argument eq "") ||
			($argument =~ /\s/ && $command ne "search")
		) {
			chomp $line;
			$line =~ s/\s*$//;
			$line =~ s/^\s*//;
			incorrect_command_message("$line");
			next;
		}

		if ($command eq "quit") {
			print "Thanks for shopping at mekong.com.au.\n";
			last;
		}
		if ($command eq "login") {
			$login = login_command($argument);
			next;
		} elsif ($command eq "new_account") {
			$login = new_account_command($argument);
			next;
		} elsif ($command eq "search") {
			search_command($argument);
			next;
		} elsif ($command eq "details") {
			details_command($argument);
			next;
		}
		
		if (!$login) {
			print "Not logged in.\n";
			next;
		}
		
		if ($command eq "basket") {
			basket_command($login);
		} elsif ($command eq "add") {
			add_command($login, $argument);
		} elsif ($command eq "drop") {
			drop_command($login, $argument);
		} elsif ($command eq "checkout") {
			#checkout_command($login);
		} elsif ($command eq "orders") {
			orders_command($login);
		} else {
			warn "internal error: unexpected command $command";
		}
	}
}

sub login_command {
	my ($login) = @_;
	if (!legal_login($login)) {
		print "$last_error\n";
		return "";
	}
	if (!-r "$users_dir/$login") {
		print "User '$login' does not exist.\n";
		return "";
	}
	printf "Enter password: ";
	my $pass = <STDIN>;
	chomp $pass;
	if (!authenticate($login, $pass)) {
		print "$last_error\n";
		return "";
	}
	$login = $login;
	print "Welcome to mekong.com.au, $login.\n";
	return $login;
}

sub new_account_command {
	my ($login) = @_;
	if (!legal_login($login)) {
		print "$last_error\n";
		return "";
	}
	if (-r "$users_dir/$login") {
		print "Invalid user name: login already exists.\n";
		return "";
	}
	if (!open(USER, ">$users_dir/$login")) {
		print "Can not create user file $users_dir/$login: $!";
		return "";
	}
	foreach $description (@new_account_rows) {
		my ($name, $label)  = split /\|/, $description;
		next if $name eq "login";
		my $value;
		while (1) {
			print "$label ";
			$value = <STDIN>;
			exit 1 if !$value;
			chomp $value;
			if ($name eq "password" && !legal_password($value)) {
				print "$last_error\n";
				next;
			}
			last if $value =~ /\S+/;
		}
		$user_details{$name} = $value;
		print USER "$name=$value\n";
	}
	close(USER);
	print "Welcome to mekong.com.au, $login.\n";
	return $login;
}

sub search_command {
	my ($search_string) = @_;
	$search_string =~ s/\s*$//;
	$search_string =~ s/^\s*//;
	search_command1(split /\s+/, $search_string);
}

sub search_command1 {
	my (@search_terms) = @_;
	my @matching_isbns = search_books1(@search_terms);
	if ($last_error) {
		print "$last_error\n";
	} elsif (@matching_isbns) {
		print_books(@matching_isbns);
	} else {
		print "No books matched.\n";
	}
}

sub details_command {
	my ($isbn) = @_;
	our %book_details;
	if (!legal_isbn($isbn)) {
		print "$last_error\n";
		return;
	}
	if (!$book_details{$isbn}) {
		print "Unknown isbn: $isbn.\n";
		return;
	}
	print_books($isbn);
	foreach $attribute (sort keys %{$book_details{$isbn}}) {
		next if $attribute =~ /Image|=|^(|price|title|authors|productdescription)$/;
		print "$attribute: $book_details{$isbn}{$attribute}\n";
	}
	my $description = $book_details{$isbn}{productdescription} or return;
	$description =~ s/\s+/ /g;
	$description =~ s/\s*<p>\s*/\n\n/ig;
	while ($description =~ s/<([^">]*)"[^"]*"([^>]*)>/<$1 $2>/g) {}
	$description =~ s/(\s*)<[^>]+>(\s*)/$1 $2/g;
	$description =~ s/^\s*//g;
	$description =~ s/\s*$//g;
	print "$description\n";
}

sub basket_info{
	my ($login) = @_;
	if(!defined $login){
		return "<div class='alert alert-warning'>Your have to login!</div>";
	}
	my @basket_isbns = read_basket($login);
	my $total_price;
	if (!@basket_isbns) {
		return "<div class='alert alert-info'>Your basket is empty.</div>";
	} else {
		#print_books(@basket_isbns);
		#printf "Total: %11s\n", sprintf("\$%.2f", total_books(@basket_isbns));
		$total_price=total_books(@basket_isbns);
		
		my $descriptions = "";
		our %book_details;
		$descriptions .=qq(<h1 style="text-align:left;">Your basket...</h1><table class="table table-hover">);
		foreach $isbn (@basket_isbns) {
		die "Internal error: unknown isbn $isbn in print_books\n" if !$book_details{$isbn}; # shouldn't happen
		my $title = $book_details{$isbn}{title} || "";
		my $authors = $book_details{$isbn}{authors} || "";
		my $thumb_url = $book_details{$isbn}{smallimageurl} || "";
		my $price = $book_details{$isbn}{price} || "";
		$authors =~ s/\n([^\n]*)$/ & $1/g;
		$authors =~ s/\n/, /g;
		$descriptions .= qq(<tr><td><a href="mekong.cgi?isbn=$isbn"><div class="book_thumb"><img class="book_thumb_img" src="$thumb_url"></div></a></td><td><a href="mekong.cgi?isbn=$isbn">$title</a><br><br><br>$authors</td><td><div class="book_price_small"><table cellpadding="10"><tr><td>$price</td></tr><tr><td><button type="button" class="btn btn-danger" data-loading-text="Deleting" style="text-align:bottom;" onclick="dropfrombasket('$isbn')">Delete</button></td></tr></table></div></td><tr>);
	}
	$descriptions .= qq(<tr><td><h2>Total</h2></td><td><br><br><br></td><td><div class="book_price_small"><table cellpadding="10"><tr><td>\$$total_price</td></tr><tr><td><button type="button" class="btn btn-primary" data-toggle="modal" data-target="#checkOutWindow" style="text-align:bottom;">Check out</button></td></tr></table></div></td><tr></table>);
	return $descriptions;
	}
}

sub add_command {
	my ($login,$isbn) = @_;
	our %book_details;
	#if (!legal_isbn($isbn)) {
	#	print "$last_error\n";
	#	return;
	#}
	if (!$book_details{$isbn}) {
		print "Unknown isbn: $isbn.\n";
		return;
	}
	add_basket($login, $isbn);
}

sub drop_command {
	my ($login,$isbn) = @_;
	my @basket_isbns = read_basket($login);
	#if (!legal_isbn($isbn)) {
	#	print "$last_error\n";
	#	return;
	#}
	if (!grep(/^$isbn$/, @basket_isbns)) {
		print "Isbn $isbn not in shopping basket.\n";
		return;
	}
	return delete_basket($login, $isbn);
}

sub checkout_command {
	my ($login,$credit_card_number, $expiry_date) = @_;
	my @basket_isbns = read_basket($login);
	if (!@basket_isbns) {
		print "Your shopping basket is empty.\n";
		return;
	}
	if(! legal_credit_card_number($credit_card_number)){
			return 0;
	}
	if(! legal_expiry_date($expiry_date)){
		return 0;
	}
	return finalize_order($login, $credit_card_number, $expiry_date);
}

sub orders_command {
	my ($login) = @_;
	print "\n";
	foreach $order (login_to_orders($login)) {
		my ($order_time, $credit_card_number, $expiry_date, @isbns) = read_order($order);
		$order_time = localtime($order_time);
		print "Order #$order - $order_time\n";
		print "Credit Card Number: $credit_card_number (Expiry $expiry_date)\n";
		print_books(@isbns);
		print "\n";
	}
}

# print descriptions of specified books
sub print_books(@) {
	my @isbns = @_;
	print get_book_descriptions(@isbns);
}

# return descriptions of specified books
sub get_book_descriptions {
	my @isbns = @_;
	my $descriptions = "";
	our %book_details;
	$descriptions .=qq(<table class="table table-hover">);
	foreach $isbn (@isbns) {
		die "Internal error: unknown isbn $isbn in print_books\n" if !$book_details{$isbn}; # shouldn't happen
		my $title = $book_details{$isbn}{title} || "";
		my $authors = $book_details{$isbn}{authors} || "";
		my $thumb_url = $book_details{$isbn}{smallimageurl} || "";
		my $price = $book_details{$isbn}{price} || "";
		$authors =~ s/\n([^\n]*)$/ & $1/g;
		$authors =~ s/\n/, /g;
		#$descriptions .= sprintf "%s %7s %s - %s\n", $isbn, $book_details{$isbn}{price}, $title, $authors;
		$descriptions .= qq(<tr><td><a href="mekong.cgi?isbn=$isbn"><div class="book_thumb"><img class="book_thumb_img" src="$thumb_url"></div></a></td><td><a href="mekong.cgi?isbn=$isbn">$title</a><br><br><br>$authors</td><td><div class="book_price_small"><table cellpadding="10"><tr><td>$price</td></tr><tr><td><button type="button" class="btn btn-info" style="text-align:bottom;" onclick="addintobasket('$isbn')">Add to basket</button></td></tr></table></div></td><tr>);
	}
	$descriptions .= qq(</table>);
	return $descriptions;
}

sub set_global_variables {	
    $cgi=new CGI;
	$base_dir = ".";
	$books_file = "$base_dir/books.json";
	$orders_dir = "$base_dir/orders";
	$baskets_dir = "$base_dir/baskets";
	$users_dir = "$base_dir/users";
	$pending_users_dir="$base_dir/pending_users";
	$last_error = undef;
	$last_alert = undef;
	$error_by = undef;
	%user_details = ();
	%book_details = ();
	%attribute_names = ();
	@new_account_rows = (
		  'login|Login:|10',
		  'password|Password:|10',
		  'name|Full Name:|50',
		  'street|Street:|50',
		  'city|City/Suburb:|25',
		  'state|State:|25',
		  'postcode|Postcode:|25',
		  'email|Email Address:|35'
		  );
}


sub incorrect_command_message {
	my ($command) = @_;
	print "Incorrect command: $command.\n";
	print <<eof;
Possible commands are:
login <login-name>
new_account <login-name>                    
search <words>
details <isbn>
add <isbn>
drop <isbn>
basket
checkout
orders
quit
eof
}


