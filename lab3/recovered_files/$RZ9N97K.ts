import { PrismaClient } from '@prisma/client/edge';
import { withAccelerate } from '@prisma/extension-accelerate';
import { verify } from 'hono/utils/jwt/jwt';
import { SignatureKey } from 'hono/utils/jwt/jws';

export class ProductController {
    private prisma: PrismaClient;
    constructor(databaseUrl: string) {
        this.prisma = new PrismaClient({
            datasources: {
                db: {
                    url: databaseUrl
                }
            }
        }).$extends(withAccelerate()) as unknown as PrismaClient;
    }

    public addProduct = async (c: any) => {
        try {
            const warehouseId = c.req.header('warehouseId');
            if (!warehouseId) {
                return c.json({ error: 'Warehouse ID is required' }, 400);
            }

            const token = c.req.header('token');
            if (!token) {
                return c.json({ error: 'Unauthorized' }, 401);
            }

            const user = verify(token, c.env.JWT_SECRET);
            if (!user) {
                return c.json({ error: 'Unauthorized' }, 401);
            }

            // First check if warehouse exists
            const warehouse = await this.prisma.warehouse.findUnique({
                where: { id: warehouseId }
            });

            if (!warehouse) {
                return c.json({ error: `Warehouse with ID ${warehouseId} not found` }, 404);
            }

            const body = await c.req.json();
            const { name, price, quantity, date } = body;

            if (!name || !price || !quantity || !date) {
                return c.json({ error: 'All fields are required' }, 400);
            }

            console.log('Received expiry date:', date);
            const parsedExpiry = new Date(date);
            
            if (isNaN(parsedExpiry.getTime())) {
                return c.json({ error: 'Invalid expiry date' }, 400);
            }

            return await this.prisma.$transaction(async (tx) => {
                // Check if product exists in this warehouse
                const existingProduct = await tx.product.findFirst({
                    where: {
                        name,
                        warehouseIds: { has: warehouseId }
                    }
                });

                let product;
                if (existingProduct) {
                    // Update existing product
                    product = await tx.product.update({
                        where: { id: existingProduct.id },
                        data: {
                            quantity: existingProduct.quantity + quantity
                        }
                    });
                } else {
                    // Create new product
                    product = await tx.product.create({
                        data: {
                            name,
                            price,
                            quantity,
                            expiry: parsedExpiry,
                            warehouseIds: [warehouseId]
                        }
                    });
                }

                // Update warehouse stock
                await tx.warehouse.update({
                    where: { id: warehouseId },
                    data: {
                        totalstock: {
                            increment: quantity
                        }
                    }
                });

                return c.json({
                    message: existingProduct ? 'Product updated successfully' : 'Product added successfully',
                    product
                });
            });

        } catch (error) {
            console.error('Error in addProduct:', error);
            return c.json({
                error: 'Failed to add/update product',
                details: error instanceof Error ? error.message : 'Unknown error'
            }, 500);
        }
    }

    public removeProduct = async (c: any) => {
        try {
            const warehouseId = c.req.header('warehouseId');
            if (!warehouseId) {
                return c.json({ error: 'Warehouse ID is required' }, 400);
            }

            const token = c.req.header('token');
            if (!token) {
                return c.json({ error: 'Unauthorized' }, 401);
            }

            const user = verify(token, c.env.JWT_SECRET);
            if (!user) {
                return c.json({ error: 'Unauthorized' }, 401);
            }

            const body = await c.req.json();
            const { productId } = body;

            if (!productId) {
                return c.json({ error: 'Product ID is required' }, 400);
            }

            // Find the product
            const product = await this.prisma.product.findUnique({
                where: { id: productId }
            });

            if (!product) {
                return c.json({ error: 'Product not found' }, 404);
            }

            // Remove the product from the warehouse
            await this.prisma.product.delete({
                where: { id: productId }
            });

            // Update warehouse stock
            await this.prisma.warehouse.update({
                where: { id: warehouseId },
                data: {
                    totalstock: {
                        decrement: product.quantity
                    }
                }
            });

            return c.json({ message: 'Product removed successfully' });
        } catch (error) {
            console.error('Error in removeProduct:', error);
            return c.json({
                error: 'Failed to remove product',
                details: error instanceof Error ? error.message : 'Unknown error'
            }, 500);
        }
    }
} 