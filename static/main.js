let d_json


const export_btn = document.getElementById('export_btn')
export_btn.addEventListener('click',async e=>{
    console.log(e)
    const myInit = {
        method: "GET",
        mode: "cors",
        cache: "default",
    };
    let data = await fetch('http://127.0.0.1:5000/get_xlsx',myInit)
    // let test = await data.formData()
    let a = document.createElement('a')
    let data_b = await data.blob()
    let url = URL.createObjectURL(data_b)
    a.href = url
    a.download = 'Signals.xlsx'
    document.body.appendChild(a)
    a.click()
    setTimeout(()=>{
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }, 0);
})

const import_btn = document.getElementById('import_btn')
import_btn.addEventListener('click',async e=>{
    console.log(e)
    let file = document.createElement('input')
    file.setAttribute('type','file')
    file.display = 'hidden'
    document.body.appendChild(file)
    file.addEventListener('change', async (e) => {
        if (e.target.files[0]) {
            let data = new FormData()
            let filedata = e.target.files[0]
            data.append('file', filedata)
            console.log('You selected ' + e.target.files[0].name);
            
            const myInit = {
                method: "POST",
                body: data,
                mode: "cors",
                cache: "default",
                redirect: 'follow'
            };
            let res = await fetch('http://127.0.0.1:5000/post_xlsx',myInit)
            console.log(res)
            location.reload()
        }

    })
    file.click()



})

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
addEventListener("load",async (event) =>  {
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
        if (signal.meters[0]){
            status.innerHTML = signal.meters[0].online_status || '&#9203'
        } else {
            status.innerHTML = 'no_meter'
        }
        status.setAttribute('title','Not Updated')
        entry.append(status)
        
        let comm = document.createElement('td')
        comm.innerHTML = signal.modem_online || '&#9203'
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
        ts.innerHTML = signal.updated_at ||'00:00:00'
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