const building = "Palladium";
const machinecount = 10;
const status = "available";

washerHTML = "";
dryerHTML = "";

for(let i=0; i<=machinecount; i++){
    washerHTML += <p>Washer ${i}: ${status}</p>
    dryerHTML += <p>Dryer ${i}: ${status}</p>
}

document.getElementById("washers").innerHTML = washerHTML;
document.getElementById("dryers").innerHTML = dryerHTML;