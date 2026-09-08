import { PrismaClient } from "@prisma/client/edge";
import { withAccelerate } from "@prisma/extension-accelerate";
import { sign } from "hono/utils/jwt/jwt";
import { SignatureKey } from "hono/utils/jwt/jws";

export class SignController {
    private prisma: PrismaClient;

    constructor(c: any) {
        const databaseUrl = (c.env as { DATABASE_URL: string }).DATABASE_URL;
        const prismaClient = new PrismaClient({
            datasourceUrl: databaseUrl
        });

        this.prisma = prismaClient.$extends(withAccelerate()) as unknown as PrismaClient;
    }

    public signup = async (c: any) => {
        let body;
        try {
            body = await c.req.json();
        } catch (error) {
            return c.json({ error: "Invalid JSON body" }, 400);
        }

        if (!body.username || !body.email || !body.password || !body.role) {
            return c.json({ error: "Missing required fields" }, 400);
        }

        const existingUser = await this.prisma.user.findUnique({
            where: {
                username: body.username
            }
        });

        if (existingUser) {
            return c.json({ error: "Username already exists" }, 400);
        }

        const user = await this.prisma.user.create({
            data: {
                email: body.email,
                username: body.username,
                password: body.password,
                role: body.role,
            }
        });

        const token: string = await sign({ userId: user.id, username: user.username, role: user.role }, c.env.JWT_SECRET);
        c.res.headers.set('Set-Cookie', `token=${token}; role=${user.role}; HttpOnly`);
        return c.json({ msg: "Signup Completed", token, id: user.id, role: user.role });
    };

    public signin = async (c: any) => {
        let body;
        try {
            body = await c.req.json();
        } catch (error) {
            return c.json({ error: "Invalid JSON body" }, 400);
        }

        if (!body.username || !body.password) {
            return c.json({ error: "Missing required fields" }, 400);
        }

        const user = await this.prisma.user.findUnique({
            where: {
                username: body.username,
                password: body.password
            }
        });

        if (!user || user.password !== body.password) {
            return c.json({ error: "Invalid username or password" }, 400);
        }

        const token: string = await sign({ userId: user.id, username: user.username, role: user.role }, c.env.JWT_SECRET);
        c.res.headers.set('Set-Cookie', `token=${token}; role=${user.role}; HttpOnly`);
        return c.json({ msg: "Signin Successful", token, id: user.id, role: user.role });
    };
} 