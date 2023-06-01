

// get data from request
async function get_data(){
    const myInit = {
        method: "GET",
        headers: {
            Accept: "application/json",
        },
        mode: "cors",
        cache: "default",
    };
    const data = await fetch('http://127.0.0.1:5000/get_data',myInit)
    console.log(data)
    return data
}
addEventListener("load",async event =>  {
    const table_data = document.getElementById('list')
    const data = await get_data()
    let d_json = await data.json()
    d_json.forEach(signal => {
        let entry = document.createElement('tr')

        let id = document.createElement('th')
        id.setAttribute('scope','row')
        id.innerHTML = signal.cog_id
        entry.append(id)

        let entry_name = document.createElement('td')
        entry_name.innerHTML = signal.name
        entry.append(entry_name)

        let status = document.createElement('td')
        if (signal.status == 'registered') {
            status.innerHTML = '&#9889'
            status.setAttribute('title','Recieving Power')
        }
        if (signal.status == 'unregistered with no replacement') {
            status.innerHTML = '&#10060'
            status.setAttribute('title','Disconnected')
        }
        entry.append(status)

        let comm = document.createElement('td')


        table_data.append(entry)
    });


})



// respond to event loops for sorts and filters

// begin running/listening to updates as they come in

// continuously have up to date data

// have a few interaction features

// only refresh display when requested

// export to excel functionality


// function update(){
//     handler = new EventSource('http://localhost:5000/listen')

//     handler.
// }