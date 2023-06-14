let d_json

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
    d_json = await data.json()
    d_json.forEach(signal => {
        let entry = document.createElement('tr')
        entry.id = signal.cog_id

        let id = document.createElement('th')
        id.setAttribute('scope','row')
        id.innerHTML = signal.cog_id
        entry.append(id)

        let entry_name = document.createElement('td')
        entry_name.innerHTML = signal.name
        entry.append(entry_name)

        let status = document.createElement('td')
        sig_stat = signal.meters[0].status
        if (sig_stat == 'registered') {
            status.innerHTML = '&#9889'
            status.setAttribute('title','Recieving Power')
        }
        if (sig_stat == 'unregistered with no replacement') {
            status.innerHTML = '&#10060'
            status.setAttribute('title','Disconnected')
        }
        entry.append(status)

        let comm = document.createElement('td')
        entry.append(comm)

        let ip = document.createElement('td')
        ip.innerHTML = signal.ip
        entry.append(ip)


        let esi = document.createElement('td')
        esi.innerHTML = signal.meters[0].esi_id
        entry.append(esi)


        table_data.append(entry)
    });


})



// respond to event loops for sorts and filters

// begin running/listening to updates as they come in

// continuously have up to date data

// have a few interaction features

// only refresh display when requested

// export to excel functionality

addEventListener('load',update)
function update(){
    handler = new EventSource('http://127.0.0.1:5000/listen')

    handler.onmessage = (e) => {
        const meter_string = e.data
        const meter_obj = JSON.parse(e.data)
        const table_data = document.getElementById('list')
        let meters = table_data.children
        meters = Array.from(meters)
        
        meters.forEach(meter =>{
            if (String(meter.children[5].innerHTML) == String(meter_obj.esi_id)){
                meter.children[2].innerHTML=meter_obj.online_status
            }
        })
    }

    handler.addEventListener("ping_comm", (e)=>{
        const com_obj = JSON.parse(e.data)
        const table_data = document.getElementById('list')
        let signals = table_data.children
        signals = Array.from(signals)
        
        signals.forEach(signal =>{
            if (Number(signal.id) == com_obj.cog_id){
                signal.children[3].innerHTML=com_obj.modem_online
            }
        })
    })
}