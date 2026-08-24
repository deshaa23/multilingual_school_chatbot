import api from "./api";

export const sendMessage = async (question) => {

    const response = await api.post("/chat1", {
        question,
    });

    return response.data;
};