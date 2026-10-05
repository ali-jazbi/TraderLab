import { readFile } from "node:fs/promises";
import { neon } from "@neondatabase/serverless";

if (!process.env.DATABASE_URL) throw new Error("Set DATABASE_URL in .env.local first.");
const schema = await readFile(new URL("../db/schema.sql", import.meta.url), "utf8");
const divider = schema.indexOf("CREATE OR REPLACE FUNCTION");
const statements = schema.slice(0, divider).replace(/--[^\n]*/g, "").split(";").filter(s => s.trim());
statements.push(schema.slice(divider));
const sql = neon(process.env.DATABASE_URL);
await sql.transaction(statements.map(statement => sql.query(statement)));
console.log("TraderLab database tables and transactional ingest function are ready.");
