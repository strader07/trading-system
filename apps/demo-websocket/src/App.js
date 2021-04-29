import React from 'react';

// import socket class
import Socket from './socket';


export default class App extends React.Component {
    constructor(props) {
        super(props);

        // state variables
        this.state = {
            connected: false,
            timestamp: "Listening to websocket!",
        }
    }

    // componentDidMount is a react life-cycle method that runs after the component
    //   has mounted.
    componentDidMount() {
        // establish websocket connection to backend server.
        let ws = new WebSocket('wss://demo.ftx.dev.muwazana.com/ws');

        // create and assign a socket to a variable.
        let socket = this.socket = new Socket(ws);

        // handle connect and discconnect events.
        socket.on('connect', this.onConnect);
        socket.on('disconnect', this.onDisconnect);

        /* EVENT LISTENERS */
        // event listener to handle 'timestamp' from a server
        socket.on('public:timestamp', this.onPublicTimestamp);
    }

    // onConnect sets the state to true indicating the socket has connected
    //    successfully.
    onConnect = () => {
        this.setState({connected: true});
    }

    // onDisconnect sets the state to false indicating the socket has been
    //    disconnected.
    onDisconnect = () => {
        this.setState({connected: false});
    }

    onPublicTimestamp = (data) => {
        this.setState({timestamp: data})
    }

    // render returns the JSX (UI elements).
    render() {
        return (
            <div>
                <h1>{this.state.timestamp}</h1>
            </div>
        )
    }
}
