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
    a.download = 'Radar.xlsx'
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

async function get_data(){
    const myInit = {
        method: "GET",
        headers: {
            Accept: "application/json",
        },
        mode: "cors",
        cache: "default",
    };
    const data = await fetch('http://127.0.0.1:5000/get_radar_data',myInit)
    console.log(data)
    return data
}
addEventListener("load", async (event) =>{
    const table_data = document.getElementById('list')
    const data = await get_data()
    d_json = await data.json()
    d_json.forEach(intersection => {
        let entry = document.createElement('tr')
        entry.id = intersection.cog_id

        let id = document.createElement('th')
        id.setAttribute('scope','row')
        id.innerHTML = intersection.cog_id
        entry.append(id)

        let entry_name = document.createElement('td')
        entry_name.innerHTML = intersection.name
        entry.append(entry_name)

        let entry_ip = document.createElement('td')
        entry_ip.innerHTML = intersection.ip
        entry.append(entry_ip)

        let radar_type = document.createElement('td')
        radar_type.innerHTML = intersection.radar_type
        entry.append(radar_type)

        let ccu_serial = document.createElement('td')
        ccu_serial.innerHTML = intersection.ccu_serial
        entry.append(ccu_serial)

        let ccu_version = document.createElement('td')
        ccu_version.innerHTML = intersection.ccu_version
        entry.append(ccu_version)

        let ccu_mac = document.createElement('td')
        ccu_mac.innerHTML = intersection.ccu_mac
        entry.append(ccu_mac)

        let biu = document.createElement('td')
        biu.innerHTML = intersection.biu
        entry.append(biu)
        
        let sensor1 = document.createElement('td')
        sensor1.innerHTML = intersection.sensor1
        entry.append(sensor1)

        let sensor2 = document.createElement('td')
        sensor2.innerHTML = intersection.sensor2
        entry.append(sensor2)

        let sensor3 = document.createElement('td')
        sensor3.innerHTML = intersection.sensor3
        entry.append(sensor3)

        let sensor4 = document.createElement('td')
        sensor4.innerHTML = intersection.sensor4
        entry.append(sensor4)

        let sensor5 = document.createElement('td')
        sensor5.innerHTML = intersection.sensor5
        entry.append(sensor5)

        let sensor6 = document.createElement('td')
        sensor6.innerHTML = intersection.sensor6
        entry.append(sensor6)

        let sensor7 = document.createElement('td')
        sensor7.innerHTML = intersection.sensor7
        entry.append(sensor7)

        let sensor8 = document.createElement('td')
        sensor8.innerHTML = intersection.sensor8
        entry.append(sensor8)

        table_data.append(entry)

    });
})