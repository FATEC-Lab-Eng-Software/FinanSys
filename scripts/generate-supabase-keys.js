import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

function fail(message, exitCode = 1) {
	console.error(`Erro: ${message}`);
	process.exit(exitCode);
}

function resolveEnvPath(args) {
	const envFileIndex = args.indexOf('--env-file');

	if (envFileIndex === -1) {
		return path.join(rootDir, '.env');
	}

	const envFile = args[envFileIndex + 1];
	if (!envFile || envFile.startsWith('--')) {
		fail('--env-file exige o caminho de um arquivo.');
	}

	return path.resolve(envFile);
}

function parseEnvValue(value) {
	const trimmedValue = value.trim();

	if (
		(trimmedValue.startsWith('"') && trimmedValue.endsWith('"')) ||
		(trimmedValue.startsWith("'") && trimmedValue.endsWith("'"))
	) {
		return trimmedValue.slice(1, -1);
	}

	return trimmedValue.replace(/\s+#.*$/, '');
}

function getEnvValue(content, key) {
	const regex = new RegExp(`^${key}=(.*)$`, 'm');
	const match = content.match(regex);

	return match ? parseEnvValue(match[1]) : '';
}

function setEnvValue(content, key, value) {
	const regex = new RegExp(`^${key}=.*$`, 'm');
	if (regex.test(content)) {
		return content.replace(regex, `${key}=${value}`);
	}

	const separator = content.length > 0 && !content.endsWith('\n') ? '\n' : '';
	return `${content}${separator}${key}=${value}\n`;
}

function createToken(role, secret) {
	const now = Math.floor(Date.now() / 1000);
	const encode = (value) => Buffer.from(JSON.stringify(value)).toString('base64url');
	const header = encode({ alg: 'HS256', typ: 'JWT' });
	const payload = encode({
		role,
		aud: 'authenticated',
		iss: 'supabase',
		iat: now,
		exp: now + 315360000,
	});
	const signature = crypto
		.createHmac('sha256', secret)
		.update(`${header}.${payload}`)
		.digest('base64url');

	return `${header}.${payload}.${signature}`;
}

const args = process.argv.slice(2);
const allowedArgs = new Set(['--force', '--env-file']);
for (let index = 0; index < args.length; index += 1) {
	if (!allowedArgs.has(args[index])) {
		fail(`argumento desconhecido: ${args[index]}`);
	}
	if (args[index] === '--env-file') index += 1;
}

const envPath = resolveEnvPath(args);
const shouldForce = args.includes('--force');

if (!fs.existsSync(envPath)) {
	fail(`arquivo .env não encontrado em ${envPath}. Copie .env.example para .env antes de continuar.`);
}

const envContent = fs.readFileSync(envPath, 'utf8');
const jwtSecret = getEnvValue(envContent, 'JWT_SECRET');

if (!jwtSecret) {
	fail('JWT_SECRET não está definido no arquivo .env. Defina o segredo antes de gerar as chaves.');
}
if (jwtSecret.length < 32) {
	fail('JWT_SECRET precisa ter pelo menos 32 caracteres.');
}

const existingAnonKey = getEnvValue(envContent, 'ANON_KEY');
const existingServiceRoleKey = getEnvValue(envContent, 'SUPABASE_SERVICE_ROLE_KEY');
if (!shouldForce && (existingAnonKey || existingServiceRoleKey)) {
	fail('chaves Supabase já existem no .env. Use --force somente se quiser regenerá-las após trocar JWT_SECRET.');
}

let updatedEnv = setEnvValue(envContent, 'ANON_KEY', createToken('anon', jwtSecret));
updatedEnv = setEnvValue(
	updatedEnv,
	'SUPABASE_SERVICE_ROLE_KEY',
	createToken('service_role', jwtSecret),
);

fs.writeFileSync(envPath, updatedEnv, 'utf8');
console.log('Chaves Supabase geradas com sucesso no .env.');
console.log('As chaves não foram exibidas no terminal.');
