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
        status.innerHTML = '&#9203'
        status.setAttribute('title','Not Updated')
        entry.append(status)

        let comm = document.createElement('td')
        entry.append(comm)

        let ip = document.createElement('td')
        ip.innerHTML = signal.ip
        entry.append(ip)


        let esi = document.createElement('td')
        if (signal.meters[0]){
            esi.innerHTML = signal.meters[0].esi_id

        } else {
            esi.innerHTML = 'N/A'
        }
        entry.append(esi)

        let ts = document.createElement('td')
        ts.innerHTML = '00:00:00'
        entry.append(ts)


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

    handler.addEventListener('oncor', (e) => {
        const meter_string = e.data
        const meter_obj = JSON.parse(e.data)
        const table_data = document.getElementById('list')
        let meters = table_data.children
        meters = Array.from(meters)
        
        meters.forEach(meter =>{
            if (String(meter.id) == String(meter_obj.cog_id)){
                meter.children[2].innerHTML=meter_obj.online_status
                meter.children[2].setAttribute('title','updated')
                meter.children[5].innerHTML=meter_obj.esi_id
            }
        })
    })

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
    handler.addEventListener("timestamp", (e)=>{
        const com_obj = JSON.parse(e.data)
        const table_data = document.getElementById('list')
        let signals = table_data.children
        signals = Array.from(signals)
        
        signals.forEach(signal =>{
            if (Number(signal.id) == com_obj.cog_id){
                signal.children[6].innerHTML=com_obj.time
            }
        })
    })
}