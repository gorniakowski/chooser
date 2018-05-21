function check_passwd(form){
    if (form.password.value != form.confirmation.value){
        $(".alert").alert('close');
        $("form").prepend("<div class =\"alert alert-primary border text-center\" role=\"alert\"> Password do not match </div>");
        form.password.focus();
        return false;
    }
    else{
        return true;
    }

}