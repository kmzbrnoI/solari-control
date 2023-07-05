#ifndef __SPI_H__
#define __SPI_H__

void spi_init(void);
void spi_write(uint8_t* data, uint8_t size);
void spi_read(uint8_t* data, uint8_t size);

#endif
