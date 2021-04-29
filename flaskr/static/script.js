function addUser(e) {
  //  console.log("HIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII");
    e.preventDefault(s);
    const form = document.querySelector('form[name="addNewUser"]');
    const name = form.elements['name'].value;
    const monthly_budget = form.elements['monthly_budget'].value;
    console.log("user: " + name);
    console.log("monthly budget: " + monthly_budget);
    datatosend = [name, monthly_budget];
    console.log("before runpyscript");
    result = runPyScript(datatosend);
    console.log('Got back ' + result);
    
}

function runPyScript(input){
    console.log("running runPyScript");
    var jqXHR = $.ajax({
        type: "POST",
        url: "/addUser",
        async: false,
        data: { mydata: input }
    });
    console.log("responseText:");
    return jqXHR.responseText;
}