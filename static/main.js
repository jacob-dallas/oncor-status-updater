mainDiv = document.getElementById('status')

status_text = document.createElement('p')
status_text.innerHTML = 'here'
mainDiv.append(status_text)

function update(){
    handler = new EventSource('http://localhost:5000/listen')

    handler.
}