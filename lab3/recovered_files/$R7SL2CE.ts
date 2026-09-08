import { PrismaClient } from '@prisma/client/edge';
import { withAccelerate } from '@prisma/extension-accelerate';
import { SignatureKey } from 'hono/utils/jwt/jws';
import { verify } from 'hono/utils/jwt/jwt';
import { Context } from 'hono';

export class WarehouseController {
    private prisma: PrismaClient;

    constructor(databaseUrl: string, private jwtSecret: SignatureKey) {
        const prismaClient = new PrismaClient({
            datasources: {
                db: {
                    url: databaseUrl
                }
            }
        });
        this.prisma = prismaClient.$extends(withAccelerate()) as unknown as PrismaClient;
    }

    public getWarehouses = async (c: any) => {
        try {
            const authHeader = c.req.header('Authorization');
            const role = c.req.header('role');

            console.log('Auth Header:', authHeader); // Debug log
            console.log('Role:', role); // Debug log

            if (!authHeader || !authHeader.startsWith('Bearer ')) {
                return c.json({ error: 'No token provided or invalid format' }, 401);
            }

            const token = authHeader.split(' ')[1];

            if (!token) {
                return c.json({ error: 'Token is missing' }, 401);
            }

            try {
                const decoded = await verify(token, this.jwtSecret) as { userId: string };
                console.log('Decoded token:', decoded); // Debug log

                if (!decoded.userId) {
                    return c.json({ error: 'Invalid token payload' }, 401);
                }

                if (role === 'owner') {
                    const user = await this.prisma.user.findUnique({
                        where: { id: decoded.userId },
                        select: { warehouseIds: true }
                    });

                    if (!user) {
                        return c.json({ error: 'User not found' }, 404);
                    }

                    const warehouses = await this.prisma.warehouse.findMany({
                        where: {
                            id: { in: user.warehouseIds }
                        }
                    });

                    return c.json(warehouses);
                }

                // For admin role, return all warehouses
                const warehouses = await this.prisma.warehouse.findMany();
                return c.json(warehouses);

            } catch (verifyError) {
                console.error('Token verification failed:', verifyError);
                return c.json({ 
                    error: 'Invalid token',
                    details: verifyError instanceof Error ? verifyError.message : 'Unknown error'
                }, 401);
            }
        } catch (error) {
            console.error('Error in getWarehouses:', error);
            return c.json({ 
                error: 'Failed to fetch warehouses',
                details: error instanceof Error ? error.message : 'Unknown error'
            }, 500);
        }
    }

    public deleteWarehouse = async (c: any) => {
        const warehouseId = c.req.header('warehouseId');
        if (!warehouseId) {
            c.status(400);
            return c.json({ error: "warehouseId is required" });
        }

        try {
            // Update users
            const users = await this.prisma.user.findMany({
                where: { warehouseIds: { has: warehouseId } }
            });

            for (const user of users) {
                const updatedWarehouseIds = user.warehouseIds.filter(id => id !== warehouseId);
                await this.prisma.user.update({
                    where: { id: user.id },
                    data: { warehouseIds: updatedWarehouseIds }
                });
            }

            // Delete associated products
            await this.prisma.product.deleteMany({
                where: { warehouseIds: { has: warehouseId } }
            });

            // Delete warehouse
            await this.prisma.warehouse.delete({
                where: { id: warehouseId }
            });

            return c.json({ success: true });
        } catch (error) {
            return c.json({ error: 'Failed to delete warehouse' }, 500);
        }
    }

    public recordSales = async (c: any) => {
        const warehouseId = c.req.header('warehouseId');
        if (!warehouseId) {
            c.status(400);
            return c.json({ error: 'Warehouse ID is required' });
        }

        const body = await c.req.json();
        const { productName, soldquantity } = body;

        if (!productName || !soldquantity) {
            c.status(400);
            return c.json({ error: 'Product name and quantity are required' });
        }

        if (soldquantity <= 0) {
            c.status(400);
            return c.json({ error: 'Quantity must be greater than 0' });
        }

        const product = await this.prisma.product.findFirst({
            where: {
                name: productName,
                warehouseIds: { has: warehouseId }
            }
        });

        if (!product) return c.json({ error: 'Product not found' }, 404);

        if (product.quantity < soldquantity) {
            return c.json({ error: 'Not enough quantity available' }, 400);
        }

        try {
                if (product.quantity - soldquantity <= 0) {
                const res = await this.prisma.product.delete({
                    where: { id: product.id }
                });
                await this.prisma.warehouse.update({
                    where: { id: warehouseId },
                    data: { totalstock: { decrement: product.quantity } }
                });
                return c.json(res);
            } else {
                const res = await this.prisma.product.update({
                    where: { id: product.id },
                    data: { quantity: { decrement: soldquantity } }
                });
                await this.prisma.warehouse.update({
                    where: { id: warehouseId },
                    data: { totalstock: { decrement: soldquantity } }
                });
                return c.json(res);
            }
        } catch (error) {
            console.error('Error recording sales:', error);
            return c.json({ error: 'Failed to record sales' }, 500);
        }
    }

    public create = async (c: any) => {
        try {
            const body = await c.req.json();
            const { name, location } = body;

            if (!name || !location) {
                c.status(400);
                return c.json({ error: "Name and location are required" });
            }

            const warehouse = await this.prisma.warehouse.create({
                data: {
                    name,
                    location,
                    totalstock: 0
                }
            });

            return c.json({ 
                message: 'Warehouse created successfully',
                warehouse 
            });
        } catch (error) {
            console.error('Error creating warehouse:', error);
            return c.json({ error: 'Failed to create warehouse' }, 500);
        }
    }

    public getWarehouseProducts = async (c: any) => {
        const warehouseId = c.req.header('warehouseId');
        
        if (!warehouseId) {
            return c.json({ error: "warehouseId is required" }, 400);
        }

        try {
            // Check and move expired products first
            await this.checkAndMoveExpiredProducts(warehouseId);

            // Then get remaining products
            const products = await this.prisma.product.findMany({
                where: {
                    warehouseIds: {
                        has: warehouseId
                    }
                }
            });

            return c.json(products);
        } catch (error) {
            console.error('Error fetching warehouse products:', error);
            return c.json({ error: 'Failed to fetch products' }, 500);
        }
    }

    public addWarehouse = async (c: any) => {
        const token = c.req.header('token');
        if (!token) {
            return c.json({ error: "Token is missing" }, 400);
        }

        const decoded = await verify(token, this.jwtSecret) as { 
            userId: string; 
            username: string; 
            role: string 
        };
        
        if (!decoded) {
            return c.json({ error: "Invalid token" }, 401);
        }

        try {
            const body = await c.req.json();
            
            if (!body.name || !body.location) {
                return c.json({ error: "Name and location are required" }, 400);
            }

            const warehouse = await this.prisma.warehouse.create({
                data: {
                    name: body.name,
                    location: body.location,
                    totalstock: 0
                }
            });

            const user = await this.prisma.user.findUnique({
                where: {
                    id: decoded.userId
                },
                select: {
                    warehouseIds: true
                }
            });

            if (!user) {
                return c.json({ error: "User not found" }, 404);
            }

            if (user.warehouseIds && user.warehouseIds.length > 0 && decoded.role === "manager") {
                return c.json({ msg: "Warehouse IDs already exist in the user's warehouseIds array" });
            }

            const updatedWarehouseIds = [...user.warehouseIds, warehouse.id];

            const userUpdate = await this.prisma.user.update({
                where: {
                    id: decoded.userId
                },
                data: {
                    warehouseIds: updatedWarehouseIds
                }
            });

            return c.json({ 
                msg: "Warehouse added successfully", 
                warehouse, 
                userUpdate 
            });

        } catch (error) {
            console.error('Error adding warehouse:', error);
            return c.json({ error: 'Failed to add warehouse' }, 500);
        }
    }

    public getExpiredProducts = async (c: Context) => {
        try {
            const token = c.req.header('Authorization')?.split(' ')[1];
            const warehouseId = c.req.header('warehouseId');

            if (!token) {
                return c.json({ error: 'No token provided' }, 401);
            }

            const decoded = await verify(token, this.jwtSecret) as { userId: string };

            // First check for any new expired products
            await this.checkAndMoveExpiredProducts(warehouseId!);

            // Then fetch all expired products
            const expiredProducts = await this.prisma.expiredProduct.findMany({
                where: {
                    warehouseId: warehouseId
                },
                include: {
                    warehouse: {
                        select: {
                            name: true
                        }
                    }
                },
                orderBy: {
                    expiredAt: 'desc'
                }
            });

            return c.json(expiredProducts);
        } catch (error) {
            console.error('Error fetching expired products:', error);
            return c.json({ 
                error: 'Failed to fetch expired products',
                details: error instanceof Error ? error.message : 'Unknown error'
            }, 500);
        }
    }

    private async checkAndMoveExpiredProducts(warehouseId: string) {
        try {
            const today = new Date();
            
            // Find all expired products in the warehouse
            const expiredProducts = await this.prisma.product.findMany({
                where: {
                    warehouseIds: { has: warehouseId },
                    expiry: { lt: today }
                }
            });

            // Move each expired product to expiredProduct table
            for (const product of expiredProducts) {
                await this.prisma.$transaction(async (tx) => {
                    // Create entry in expiredProduct table
                    await tx.expiredProduct.create({
                        data: {
                            name: product.name,
                            price: product.price,
                            quantity: product.quantity,
                            expiry: product.expiry,
                            warehouseId: warehouseId
                        }
                    });

                    // Update warehouse stock
                    await tx.warehouse.update({
                        where: { id: warehouseId },
                        data: {
                            totalstock: {
                                decrement: product.quantity
                            }
                        }
                    });

                    // Remove the warehouse ID from the product's warehouseIds
                    const updatedWarehouseIds = product.warehouseIds.filter(id => id !== warehouseId);
                    
                    if (updatedWarehouseIds.length === 0) {
                        // If no warehouses left, delete the product
                        await tx.product.delete({
                            where: { id: product.id }
                        });
                    } else {
                        // Update the product's warehouseIds
                        await tx.product.update({
                            where: { id: product.id },
                            data: {
                                warehouseIds: updatedWarehouseIds
                            }
                        });
                    }
                });
            }

            return expiredProducts.length;
        } catch (error) {
            console.error('Error checking expired products:', error);
            return 0;
        }
    }
} 