import {createApp} from 'vue';
import {setupCalendar} from 'v-calendar';
import App from './App.vue';
import 'v-calendar/style.css';
import './index.css';

const app = createApp(App);

app.use(setupCalendar, {});
app.mount('#root');
