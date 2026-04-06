// frontend/src/debug-api.js
// 🧪 ARQUIVO DE DEBUG - Teste suas requisições de API aqui

import { API_URL } from './config';

export const debugLogin = async (username, password) => {
    console.group('🔍 DEBUG LOGIN');
    console.log(`📍 API URL: ${API_URL}`);
    console.log(`👤 Username: ${username}`);

    try {
        // 1. Teste de conectividade
        console.log('\n1️⃣ Testando conectividade com backend...');
        const healthCheck = await fetch(`${API_URL}/`);
        const healthData = await healthCheck.json();
        console.log('✅ Backend respondeu:', healthData);

        // 2. Teste de login
        console.log('\n2️⃣ Enviando credenciais para /token...');
        const params = new URLSearchParams();
        params.append('username', username);
        params.append('password', password);

        const response = await fetch(`${API_URL}/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: params.toString(),
        });

        console.log(`📊 Status HTTP: ${response.status}`);

        const data = await response.json();
        console.log('📦 Resposta:', data);

        if (response.ok) {
            console.log('✅ LOGIN SUCESSO!');
            console.log(`🔑 Token: ${data.access_token.substring(0, 20)}...`);

            // 3. Teste de autenticação
            console.log('\n3️⃣ Testando /users/me com token...');
            const meResponse = await fetch(`${API_URL}/users/me`, {
                headers: {
                    'Authorization': `Bearer ${data.access_token}`
                }
            });

            const meData = await meResponse.json();
            console.log('👤 Dados do usuário:', meData);

            if (meResponse.ok) {
                console.log('✅ AUTENTICAÇÃO CONFIRMADA!');
            }
        } else {
            console.error('❌ LOGIN FALHOU');
            console.error('Erro:', data);
        }
    } catch (error) {
        console.error('💥 ERRO NA REQUISIÇÃO:', error);
        console.error('Detalhes:', error.message);
    }

    console.groupEnd();
};

export const testBackendConnection = async () => {
    console.group('🌐 TESTE DE CONEXÃO');
    console.log(`📍 Testando: ${API_URL}`);

    try {
        const response = await fetch(`${API_URL}/`);
        const data = await response.json();
        console.log('✅ BACKEND ONLINE:', data);
        return true;
    } catch (error) {
        console.error('❌ NÃO CONSEGUIU CONECTAR:', error.message);
        console.error('Possíveis causas:');
        console.error('  1. Backend não está rodando');
        console.error('  2. URL incorreta:', API_URL);
        console.error('  3. Problema de CORS');
        return false;
    } finally {
        console.groupEnd();
    }
};
