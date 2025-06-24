import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
    vus: 200,
    duration: '60s',
};

const BASE_URL = 'http://localhost:8000';

export default function () {
    if (Math.random() < 0.5) {
        let payload = JSON.stringify({
            vendor: Math.random() < 0.5 ? "sync" : "async",
            name: "Test User",
            email: "test@example.com"
        });
        let res = http.post(`${BASE_URL}/jobs`, payload, { headers: { 'Content-Type': 'application/json' } });
        check(res, { 'POST /jobs status 200': (r) => r.status === 200 });
        sleep(0.1);
    } else {
        let fake_id = '00000000-0000-4000-8000-000000000000';
        let res = http.get(`${BASE_URL}/jobs/${fake_id}`);
        check(res, { 'GET /jobs status 200': (r) => r.status === 200 });
        sleep(0.1);
    }
}