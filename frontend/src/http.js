import axios from "axios";
import {config} from "./config";

const client = axios.create({
    baseURL: config.baseHttp,
    timeout: 15000,
});
client.interceptors.request.use(
    function (config) {
        return config;
    },
    function (err) {
        return Promise.reject(err);
    }
);
client.interceptors.response.use(
    function (response) {
        return response;
    },
    function (err) {
        return Promise.reject(err);
    }
);

const localClient = axios.create({
    baseURL: "",
    timeout: 15000,
});
localClient.interceptors.request.use(
    function (config) {
        return config;
    },
    function (err) {
        return Promise.reject(err);
    }
);
localClient.interceptors.response.use(
    function (response) {
        return response;
    },
    function (err) {
        return Promise.reject(err);
    }
);

export {
    client,
    localClient,
}